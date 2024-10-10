import json
import os
import boto3
import logging
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa o cliente Rekognition
rekognition = boto3.client("rekognition", region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Obtém o nome da pasta da variável de ambiente
FOLDER_NAME = os.getenv("FOLDER_NAME", "myphotos")

def check_env_vars():
    """Verifica se todas as variáveis de ambiente obrigatórias estão definidas."""
    required_vars = ['AWS_REGION', 'BUCKET_NAME', 'FOLDER_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Faltando variáveis de ambiente: {', '.join(missing_vars)}")

def detect_face_emotions(bucket_name: str, image_name: str) -> dict:
    """Detecta emoções faciais em uma imagem armazenada no S3 usando o AWS Rekognition."""
    # Verifica se as variáveis de ambiente estão definidas
    check_env_vars()

    if not bucket_name or not image_name:
        logger.error("Nome do bucket ou da imagem não pode ser vazio.")
        return {"error": "Nome do bucket ou da imagem não pode ser vazio."}

    try:
        # Inclui o caminho da pasta na chave da imagem
        full_image_path = f"{FOLDER_NAME}/{image_name}"
        response = rekognition.detect_faces(
            Image={"S3Object": {"Bucket": bucket_name, "Name": full_image_path}},
            Attributes=["ALL"]
        )
        logger.info("Resposta do Rekognition recebida com sucesso.")
    except ClientError as e:
        logger.error("Erro ao chamar a API Rekognition: %s", e)
        return {"error": "Erro ao chamar a API Rekognition", "message": str(e)}

    if not response.get("FaceDetails"):
        logger.warning("Nenhuma face detectada na imagem.")
        return {"faces": [{"position": {}, "classified_emotion": None, "classified_emotion_confidence": None}]}

    return process_faces(response["FaceDetails"])

def process_faces(face_details):
    """Processa as faces detectadas e retorna as informações formatadas."""
    face_data = {"faces": []}

    for face in face_details:
        emotions = face.get("Emotions", [])
        max_emotion = max(emotions, key=lambda e: e["Confidence"], default={"Type": None, "Confidence": 0})
        
        face_info = {
            "position": face["BoundingBox"],
            "classified_emotion": max_emotion["Type"],
            "classified_emotion_confidence": max_emotion["Confidence"]
        }

        face_data["faces"].append(face_info)

    logger.info("Processamento concluído. Total de faces detectadas: %d", len(face_data["faces"]))
    return face_data

### Funções de Manipulação das Rotas ###

def health(event, context):
    """Rota GET / - Retorna uma mensagem simples de saúde."""
    return create_response(200, {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event
    })

def vision(event, context):
    """Função que processa a solicitação para detectar emoções faciais."""
    try:
        # Verifica se as variáveis de ambiente estão definidas
        check_env_vars()

        # Extrai e valida o corpo da requisição
        body = json.loads(event.get('body', '{}'))
        bucket = body.get('bucket')
        image_name = body.get('imageName')  # Nome da imagem

        # Valida se os campos estão preenchidos
        if not bucket or not image_name:
            logger.error("Faltando o nome do bucket ou da imagem.")
            return create_response(400, {
                "error": "Faltando o nome do bucket ou da imagem."
            })

        # Verifica se o bucket é permitido
        if bucket != os.getenv('BUCKET_NAME'):
            logger.error("Bucket não permitido: %s", bucket)
            return create_response(403, "Bucket não permitido.")

        # Obtém o nome da pasta da variável de ambiente
        folder_name = os.getenv('FOLDER_NAME')
        if not folder_name:
            logger.error("FOLDER_NAME não está definido nas variáveis de ambiente.")
            return create_response(500, "Erro interno: FOLDER_NAME não definido.")

        # Chama o AWS Rekognition para detectar emoções
        result = detect_face_emotions(bucket, image_name)

        # Prepara o caminho da imagem
        image_key = f"{folder_name}/{image_name}"
        image_url = f"https://{bucket}.s3.amazonaws.com/{image_key}"

        return create_response(200, {
            "url_to_image": image_url,
            "created_image": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "faces": result
        })

    except json.JSONDecodeError:
        logger.error("JSON inválido no corpo da requisição.")
        return create_response(400, "JSON inválido no corpo da requisição.")
    except ClientError as e:
        logger.error(f"Erro ao chamar Rekognition: {e}")
        return create_response(500, "Erro ao chamar o serviço Rekognition.")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return create_response(500, "Erro interno do servidor")

def create_response(status_code, message):
    """Cria uma resposta padronizada."""
    if isinstance(message, dict):
        body = message
    else:
        body = {"message": message}
    
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }


