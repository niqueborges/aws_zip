import boto3
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
from vision_face import detect_face_emotions  # Importa a função correta que detecta emoções
# Importa a função que detecta emoções

# Carrega as credenciais do ambiente
load_dotenv()

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis para acesso
S3_BUCKET = "photogrupo3"  # Nome do bucket S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")  # Access Key ID da AWS
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")  # Secret Key da AWS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # Região AWS

# Inicializa a sessão boto3 com credenciais
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

rekognition = boto3.client("rekognition")
bedrock = boto3.client("bedrock_runtime")  # Cliente para Bedrock

def detect_labels(bucket: str, image_name: str) -> dict:
    """Detecta rótulos em uma imagem armazenada no S3 usando Rekognition."""
    try:
        image_path = f"myphotos/{image_name}"
        response = rekognition.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": image_path}},
            MaxLabels=10,
            MinConfidence=75,
        )
        return response
    except Exception as e:
        logger.error(f"Erro ao detectar rótulos: {str(e)}")
        return {"error": str(e)}

def generate_pastor_tips(labels: list) -> dict:
    """Gera dicas sobre cães pastores baseadas em rótulos detectados."""
    exclude_keywords = {"Animal", "Canine", "Mammal", "Pet", "Dog"}
    pastor_labels = [
        label for label in labels if label.get("Name") not in exclude_keywords and 
        any(category["Name"] == "Animals and Pets" for category in label.get("Categories", []))
    ]

    logger.info(f"Rótulos filtrados: {pastor_labels}")

    if pastor_labels:
        raca_nome = pastor_labels[0]["Name"]
        logger.info(f"Raça identificada: {raca_nome}")

        prompt = (
            f"Eu gostaria de Dicas sobre cães pastores como {raca_nome}. "
            "Por favor, forneça informações detalhadas seguindo a estrutura abaixo:\n"
            "Nível de Energia e Necessidades de Exercícios:\n"
            "Temperamento e Comportamento:\n"
            "Cuidados e Necessidades:\n"
            "Problemas de Saúde Comuns:\n"
        )

        native_request = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": 500,
                "temperature": 0.7,
                "topP": 0.9,
            },
        }

        logger.info(f"Enviando prompt ao Bedrock: {prompt}")

        try:
            response = bedrock.invoke_model(
                modelId="amazon.titan-text-express-v1",
                body=json.dumps(native_request),
            )

            model_response = json.loads(response["body"].read())
            bedrock_response = model_response["results"][0]["outputText"]

            logger.info(f"Resposta do Bedrock: {bedrock_response}")

            return {
                "labels": pastor_labels,
                "Dicas": bedrock_response,
            }

        except Exception as e:
            logger.error(f"Erro ao invocar o modelo: {e}")
            return {"error": str(e)}

    logger.warning("Nenhuma raça identificada.")
    return []

def validate_input(body):
    """Valida os campos obrigatórios no corpo da requisição."""
    if not body.get("bucket") or not body.get("imageName"):
        raise ValueError("Os campos 'bucket' e 'imageName' são obrigatórios.")
    return body["bucket"], body["imageName"]

def handler_pastor(event, context):
    """Processa a imagem e gera dicas sobre cães pastores."""
    try:
        body = json.loads(event["body"])
        logger.info("Event received: %s", json.dumps(event))

        # Valida e obtém bucket e nome da imagem
        bucket, image_name = validate_input(body)

        # Adiciona a pasta 'myphotos' ao nome da imagem
        image_path = f"myphotos/{image_name}"

        # Detecta emoções na imagem
        response = detect_face_emotions(bucket, image_path)
        logger.info("Rekognition response: %s", json.dumps(response))

        faces = [
            {
                "position": face["BoundingBox"],
                "classified_emotion": max(face["Emotions"], key=lambda e: e["Confidence"], default={"Type": "Unknown", "Confidence": 0})["Type"],
                "classified_emotion_confidence": max(face["Emotions"], key=lambda e: e["Confidence"], default={"Type": "Unknown", "Confidence": 0})["Confidence"],
            }
            for face in response.get("FaceDetails", [])
        ]

        # Detectando pets usando Rekognition (labels)
        rekognition_label_response = detect_labels(bucket, image_path)
        labels = rekognition_label_response.get("Labels", [])

        # Verifica se há cães pastores e gera dicas
        pastor_analysis = generate_pastor_tips(labels)
        if pastor_analysis:
            # Gera a data e hora atual em UTC
            result = {
                "url_to_image": f"https://{bucket}.s3.amazonaws.com/{image_path}",
                "created_image": datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y %H:%M:%S"),
                "faces": faces or None,
                "pets": pastor_analysis,
            }

            logger.info("Response: %s", json.dumps(result))
            return {"statusCode": 200, "body": json.dumps(result)}

        logger.info("Nenhum cão pastor detectado.")
        return {"statusCode": 200, "body": json.dumps({"message": "No pastor dogs detected"})}

    except ValueError as ve:
        logger.error(f"Valor inválido: {str(ve)}")
        return {"statusCode": 400, "body": json.dumps({"error": str(ve)})}
    except Exception as e:
        logger.error(f"Erro ao processar a imagem: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": "Failed to process the image"})}

