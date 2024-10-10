import json
import os
import logging
import boto3
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

# Obtém as variáveis de ambiente
BUCKET_NAME = os.getenv("BUCKET_NAME")
FOLDER_NAME = os.getenv("FOLDER_NAME", "myphotos")

def check_env_vars():
    """Verifica se todas as variáveis de ambiente obrigatórias estão definidas."""
    required_vars = ['AWS_REGION', 'BUCKET_NAME', 'FOLDER_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Faltando variáveis de ambiente: {', '.join(missing_vars)}")

def create_response(status_code, message):
    """Cria uma resposta padronizada."""
    return {
        "statusCode": status_code,
        "body": json.dumps({"message": message})
    }

def detect_face_emotions(bucket_name: str, image_name: str) -> dict:
    """Detecta emoções faciais em uma imagem armazenada no S3 usando o AWS Rekognition."""
    check_env_vars()  # Verifica variáveis de ambiente

    if not bucket_name or not image_name:
        logger.error("Nome do bucket ou da imagem não pode ser vazio.")
        return create_response(400, "Nome do bucket ou da imagem não pode ser vazio.")

    try:
        full_image_path = f"{FOLDER_NAME}/{image_name}"
        response = rekognition.detect_faces(
            Image={"S3Object": {"Bucket": bucket_name, "Name": full_image_path}},
            Attributes=["ALL"]
        )
        logger.info("Resposta do Rekognition recebida com sucesso.")
    except ClientError as e:
        logger.error("Erro ao chamar a API Rekognition: %s", e)
        return create_response(500, "Erro ao chamar o serviço Rekognition")

    if not response.get("FaceDetails"):
        logger.warning("Nenhuma face detectada na imagem.")
        return {"faces": []}  # Retorna uma lista vazia de faces

    return process_faces(response["FaceDetails"])

def process_faces(face_details):
    """Processa as faces detectadas e retorna as informações formatadas."""
    face_data = {"faces": []}

    for face in face_details:
        emotions = face.get("Emotions", [])
        max_emotion = max(emotions, key=lambda e: e["Confidence"], default={"Type": None, "Confidence": 0})

        face_info = {
            "bounding_box": face["BoundingBox"],
            "emotion": max_emotion["Type"],
            "confidence": max_emotion["Confidence"]
        }
        face_data["faces"].append(face_info)

    logger.info("Processamento concluído. Total de faces detectadas: %d", len(face_data["faces"]))
    return face_data

def health(event, context):
    """Rota GET / - Retorna uma mensagem simples de saúde."""
    return create_response(200, "API está funcionando!")

def vision(event, context):
    """Função que processa a solicitação para detectar emoções faciais."""
    try:
        check_env_vars()  # Verifica variáveis de ambiente

        body = json.loads(event.get('body', '{}'))
        bucket = body.get('bucket')
        image_name = body.get('imageName')

        # Valida se os campos estão preenchidos
        if not bucket or not image_name:
            logger.error("Faltando o nome do bucket ou da imagem.")
            return create_response(400, "Faltando o nome do bucket ou da imagem.")

        # Verifica se o bucket é permitido
        if bucket != BUCKET_NAME:
            logger.error("Bucket não permitido: %s", bucket)
            return create_response(403, "Bucket não permitido.")

        # Chama o AWS Rekognition para detectar emoções
        result = detect_face_emotions(bucket, image_name)

        # Prepara o caminho da imagem
        image_key = f"{FOLDER_NAME}/{image_name}"
        image_url = f"https://{bucket}.s3.amazonaws.com/{image_key}"

        return create_response(200, {
            "url_to_image": image_url,
            "created_at": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
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

# Funções principais do Lambda
def lambda_handler(event, context):
    """Função principal do Lambda que roteia a requisição para a função apropriada."""
    route = event.get('path', '')

    if route == '/':
        return health(event, context)
    elif route == '/v1/vision':
        return vision(event, context)
    else:
        return create_response(404, "Rota não encontrada.")

