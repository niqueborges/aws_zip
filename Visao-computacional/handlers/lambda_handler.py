import json  
import logging
import os
from botocore.exceptions import ClientError
from datetime import datetime
import boto3

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa a sessão boto3 com credenciais do AWS CLI
session = boto3.Session()
rekognition = session.client("rekognition")

def check_env_vars():
    """Verifica se todas as variáveis de ambiente obrigatórias estão definidas."""
    required_vars = ['BUCKET_NAME', 'FOLDER_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Faltando variáveis de ambiente: {', '.join(missing_vars)}")

def create_response(status_code, body):
    """Cria uma resposta para a API."""
    return {
        'statusCode': status_code,
        'body': json.dumps(body)
    }

def process_faces(face_details, image_url):
    """Processa os detalhes das faces retornados pela API Rekognition."""
    faces_output = []
    for face in face_details:
        faces_output.append({
            'emotion': max(face['Emotions'], key=lambda x: x['Confidence'])['Type'],
            'confidence': max(face['Emotions'], key=lambda x: x['Confidence'])['Confidence'],
            'bounding_box': face['BoundingBox']
        })
    return faces_output

def vision(event, context):
    """Detecta emoções faciais em uma imagem armazenada no S3."""
    try:
        # Verifica se as variáveis de ambiente estão definidas
        check_env_vars()

        # Log do evento recebido
        logger.info(f"Evento recebido: {event}")

        # Verifica se o corpo está presente
        if 'body' not in event or not event['body']:
            logger.error("Corpo da requisição ausente ou vazio.")
            return create_response(400, "Corpo da requisição ausente ou vazio.")
        
        # Extrai e valida o corpo da requisição
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            logger.error("JSON inválido no corpo da requisição.")
            return create_response(400, "JSON inválido no corpo da requisição.")

        bucket = body.get('bucket')
        image_name = body.get('imageName')  # A imagem deve ser 'test-happy.jpg'

        # Valida se os campos estão preenchidos
        if not bucket or not image_name:
            logger.error("Faltando o nome do bucket ou da imagem.")
            return create_response(400, {
                "error": "Faltando o nome do bucket ou da imagem."
            })

        # Código restante...
        
    except ClientError as e:
        logger.error(f"Erro ao chamar Rekognition: {e}")
        return create_response(500, "Erro ao chamar o serviço Rekognition.")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return create_response(500, "Erro interno do servidor")
