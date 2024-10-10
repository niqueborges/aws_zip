# handlers/handler_face.py
import json
import logging
import os
import boto3
import sys
from botocore.exceptions import ClientError
from dotenv import load_dotenv  # Importa a biblioteca dotenv
from datetime import datetime

# Carrega as variáveis do arquivo .env
load_dotenv()  # Isso irá carregar automaticamente as variáveis de ambiente do arquivo .env

# Inicializa o logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o caminho do diretório visao-computacional ao sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

# Inicializa o cliente Rekognition
rekognition = boto3.client("rekognition", region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Obtém o nome da pasta da variável de ambiente
FOLDER_NAME = os.getenv("FOLDER_NAME", "myphotos")  # Substitua "myphotos" pelo nome padrão desejado

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

def validate_input(body):
    """
    Valida os campos obrigatórios no corpo da requisição.

    Args:
        body (dict): O corpo da requisição.

    Returns:
        tuple: Um booleano que indica se a validação passou e um dicionário de erros, se houver.
    """
    errors = {}
    if not body.get("bucket"):
        errors["bucket"] = "O campo 'bucket' é obrigatório."
    if not body.get("imageName"):
        errors["imageName"] = "O campo 'imageName' é obrigatório."
    if not body.get("folderName") or body["folderName"] != FOLDER_NAME:
        errors["folderName"] = f"O campo 'folderName' é obrigatório e deve ser '{FOLDER_NAME}'."
    return len(errors) == 0, errors

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

def detect_face_emotions(bucket_name: str, image_path: str) -> dict:
    """Detecta emoções faciais em uma imagem armazenada no S3 usando o AWS Rekognition."""
    check_env_vars()  # Verifica variáveis de ambiente

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

    return process_faces(response["FaceDetails"])

def v1_vision(event, context):
    """
    Função para detectar emoções faciais em uma imagem armazenada no S3.
    Args:
        event (dict): Dados do evento que disparou a função.
        context (Any): Contexto de execução da função.

    Returns:
        dict: Resposta em formato JSON com os detalhes da imagem, emoções detectadas ou mensagem de erro.
    """
    # Verifica se as variáveis de ambiente estão definidas
    check_env_vars()

    try:
        body = json.loads(event.get("body", "{}"))  # Carrega o corpo da requisição
    except json.JSONDecodeError:
        logger.error("JSON inválido no corpo da requisição.")
        return create_response(400, "JSON inválido no corpo da requisição.")

    # Valida os campos obrigatórios
    is_valid, errors = validate_input(body)
    if not is_valid:
        logger.error("Erro de validação: %s", errors)
        return create_response(400, "Erro de validação", errors)

    bucket_name = body["bucket"]
    folder_name = body["folderName"]  # Espera-se que seja igual a FOLDER_NAME
    image_name = body["imageName"]
    image_path = f"{folder_name}/{image_name}"  # Usa a pasta selecionada no caminho da imagem

    # Detecta emoções na imagem
    face_data = detect_face_emotions(bucket_name, image_path)
    if "error" in face_data:
        logger.error("Erro ao detectar emoções: %s", face_data["error"])
        return create_response(500, "Erro ao detectar emoções.")

    logger.info("Processamento concluído com sucesso.")
    return {
        "statusCode": 200,
        "body": json.dumps(face_data, indent=4, ensure_ascii=True)
    }

# Função principal do Lambda
def lambda_handler(event, context):
    """Função principal do Lambda que roteia a requisição para a função apropriada."""
    route = event.get('path', '')

    if route == '/v1/vision':
        return v1_vision(event, context)
    else:
        return create_response(404, "Rota não encontrada.")
