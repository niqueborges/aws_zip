import json
import os
import boto3
import logging
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Carregar variáveis de ambiente
load_dotenv()

# Inicializa o cliente AWS Rekognition
rekognition = boto3.client('rekognition', region_name='us-east-1')

def check_env_vars():
    """Verifica se todas as variáveis de ambiente obrigatórias estão definidas."""
    required_vars = ['AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'BUCKET_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Faltando variáveis de ambiente: {', '.join(missing_vars)}")

def vision(event, context):
    """Detecta emoções faciais em uma imagem armazenada no S3."""
    try:
        # Verifica se as variáveis de ambiente estão definidas
        check_env_vars()

        # Extrai e valida o corpo da requisição
        body = json.loads(event.get('body', '{}'))
        bucket = body.get('bucket')
        image_name = body.get('imageName')

        if not bucket or not image_name:
            return create_response(400, "Faltando 'bucket' ou 'imageName' no corpo da requisição")

        # Verifica se o bucket é permitido
        if bucket != os.getenv('BUCKET_NAME'):
            return create_response(403, "Bucket não permitido.")

        # Prepara o caminho da imagem
        image_key = f"myphotos/{image_name}"
        image_url = f"https://{bucket}.s3.amazonaws.com/{image_key}"

        # Chama o AWS Rekognition para detectar emoções
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket, 'Name': image_key}},
            Attributes=['ALL']
        )

        faces_output = process_faces(response.get('FaceDetails', []), image_url)

        return create_response(200, {
            "url_to_image": image_url,
            "created_image": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "faces": faces_output
        })

    except json.JSONDecodeError:
        logger.error("JSON inválido no corpo da requisição.")
        return create_response(400, "JSON inválido no corpo da requisição")
    except ClientError as e:
        logger.error(f"Erro ao chamar Rekognition: {e}")
        return create_response(500, "Erro ao chamar o serviço Rekognition.")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return create_response(500, "Erro interno do servidor")

def process_faces(faces_detected, image_url):
    """Processa as faces detectadas e retorna a estrutura de resposta."""
    if not faces_detected:
        return [{
            "position": {
                "Height": None, "Left": None, "Top": None, "Width": None
            },
            "classified_emotion": None,
            "classified_emotion_confidence": None
        }]

    faces_output = []
    for face in faces_detected:
        emotions = face.get('Emotions', [])
        if emotions:
            primary_emotion = max(emotions, key=lambda x: x['Confidence'])
            faces_output.append({
                "position": face['BoundingBox'],
                "classified_emotion": primary_emotion['Type'],
                "classified_emotion_confidence": primary_emotion['Confidence']
            })
    return faces_output

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
