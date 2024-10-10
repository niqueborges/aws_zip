import json
import logging
import os
import boto3
from datetime import datetime
import sys
from botocore.exceptions import ClientError
from dotenv import load_dotenv  # Importa a biblioteca dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Adiciona o diretório do projeto ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importações de serviços
from services.bedrock_runtime import invoke_bedrock_model
from services.get_image import get_image_details, detect_face_emotions  # Importa as funções corretas

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa a sessão boto3 com credenciais do AWS CLI
session = boto3.Session()

rekognition = session.client("rekognition")
bedrock = session.client("bedrock-runtime")  # Cliente para Bedrock

# Obtém o nome da pasta do ambiente
FOLDER_NAME = os.getenv("FOLDER_NAME", "myphotos")  # Nome da pasta padrão

def check_env_vars():
    """Verifica se todas as variáveis de ambiente obrigatórias estão definidas."""
    required_vars = ['AWS_REGION', 'BUCKET_NAME', 'FOLDER_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Faltando variáveis de ambiente: {', '.join(missing_vars)}")

def create_response(status_code, message, data=None):
    """Cria uma resposta padronizada."""
    response_body = {"message": message}
    if data is not None:
        response_body["data"] = data
    return {
        "statusCode": status_code,
        "body": json.dumps(response_body, ensure_ascii=True)
    }

def validate_input(body: dict) -> tuple:
    """Valida os campos obrigatórios no corpo da requisição."""    
    required_keys = ("bucket", "imageName", "folderName")
    if not all(key in body for key in required_keys):
        raise ValueError("Os campos 'bucket', 'imageName' e 'folderName' são obrigatórios.")
    
    if body["folderName"] != FOLDER_NAME:
        raise ValueError(f"A pasta deve ser '{FOLDER_NAME}'.")

    return body["bucket"], body["imageName"]

def detect_labels(bucket: str, image_name: str) -> dict:
    """Detecta rótulos em uma imagem armazenada no S3 usando Rekognition."""
    image_path = f"{FOLDER_NAME}/{image_name}"
    try:
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
    return {"labels": [], "Dicas": "Nenhuma dica disponível."}

def extract_faces(response: dict) -> list:
    """Extrai as emoções das faces detectadas da resposta do Rekognition."""
    return [
        {
            "position": face["BoundingBox"],
            "classified_emotion": max(face["Emotions"], key=lambda e: e["Confidence"], default={"Type": "Unknown", "Confidence": 0})["Type"],
            "classified_emotion_confidence": max(face["Emotions"], key=lambda e: e["Confidence"], default={"Type": "Unknown", "Confidence": 0})["Confidence"],
        }
        for face in response.get("FaceDetails", [])
    ]

def detect_face_emotions(bucket_name: str, image_path: str) -> dict:
    """Detecta emoções faciais em uma imagem armazenada no S3 usando o AWS Rekognition."""
    if not bucket_name or not image_path:
        logger.error("Nome do bucket ou da imagem não pode ser vazio.")
        return create_response(400, "Nome do bucket ou da imagem não pode ser vazio.")

    try:
        response = rekognition.detect_faces(
            Image={"S3Object": {"Bucket": bucket_name, "Name": image_path}},
            Attributes=["ALL"]
        )
        logger.info("Resposta do Rekognition recebida com sucesso.")
    except ClientError as e:
        logger.error("Erro ao chamar a API Rekognition: %s", e)
        return create_response(500, "Erro ao chamar o serviço Rekognition")

    if not response.get("FaceDetails"):
        logger.warning("Nenhuma face detectada na imagem.")
        return {"faces": []}  # Retorna uma lista vazia de faces

    return extract_faces(response)

def handler_pastor(event: dict, context) -> dict:
    """Processa a imagem e gera dicas sobre cães pastores."""
    try:
        body = json.loads(event["body"])
        logger.info("Event received: %s", json.dumps(event))

        # Valida e obtém bucket, nome da imagem e nome da pasta
        bucket, image_name = validate_input(body)

        # Detecta emoções na imagem
        face_response = detect_face_emotions(bucket, f"{FOLDER_NAME}/{image_name}")
        logger.info("Rekognition face response: %s", json.dumps(face_response))

        faces = extract_faces(face_response)

        # Detectando pets usando Rekognition (labels)
        rekognition_label_response = detect_labels(bucket, image_name)
        labels = rekognition_label_response.get("Labels", [])

        # Verifica se há cães pastores e gera dicas
        pastor_analysis = generate_pastor_tips(labels)
        result = create_result(bucket, image_name, faces, pastor_analysis)

        logger.info("Response: %s", json.dumps(result))
        return create_response(200, "Processamento bem-sucedido", result)

    except ValueError as ve:
        logger.error(f"Valor inválido: {str(ve)}")
        return create_response(400, str(ve))
    except Exception as e:
        logger.error(f"Erro ao processar a imagem: {str(e)}")
        return create_response(500, "Falha ao processar a imagem")

def create_result(bucket: str, image_name: str, faces: list, pastor_analysis: dict) -> dict:
    """Cria o resultado final a ser retornado na resposta da API."""
    return {
        "url_to_image": f"https://{bucket}.s3.amazonaws.com/{FOLDER_NAME}/{image_name}",
        "created_image": datetime.now(datetime.timezone.utc).strftime("%d-%m-%Y %H:%M:%S"),
        "faces": faces or None,
        "pets": pastor_analysis,
    }

def lambda_handler(event, context):
    """Função principal do Lambda que roteia a requisição para a função apropriada."""
    route = event.get('path', '')

    if route == '/v1/vision':
        return v1_vision(event, context)  # Presumindo que v1_vision já está implementada
    elif route == '/v1/pastor':
        return handler_pastor(event, context)
    else:
        return create_response(404, "Rota não encontrada.")

# Verifica se as variáveis de ambiente estão definidas antes de iniciar o processamento
check_env_vars()
