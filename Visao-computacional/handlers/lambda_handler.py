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

        # Extrai e valida o corpo da requisição
        body = json.loads(event.get('body', '{}'))
        bucket = body.get('bucket')
        image_name = body.get('imageName')  # A imagem deve ser 'test-happy.jpg'

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

        # Prepara o caminho da imagem
        image_key = f"{folder_name}/{image_name}"
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
        return create_response(400, "JSON inválido no corpo da requisição.")
    except ClientError as e:
        logger.error(f"Erro ao chamar Rekognition: {e}")
        return create_response(500, "Erro ao chamar o serviço Rekognition.")
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return create_response(500, "Erro interno do servidor")
