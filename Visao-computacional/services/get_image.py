import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Union
import os

# Carrega o nome da pasta a partir do arquivo .env
FOLDER_NAME = os.getenv("FOLDER_NAME", "myphotos")  # Substitua "myphotos" pelo valor padrão desejado

def get_image_details(bucket_name: str, image_name: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Obtém os detalhes de uma imagem armazenada no S3.

    Args:
        bucket_name (str): O nome do bucket S3.
        image_name (str): A chave (nome) do arquivo de imagem no bucket S3.

    Returns:
        dict: Um dicionário contendo a URL da imagem e sua data de criação,
              ou uma mensagem de erro caso a operação falhe.
    """
    s3_client = boto3.client("s3")
    image_key = f"{FOLDER_NAME}/{image_name}"  # Constrói o caminho da imagem com base na pasta

    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=image_key)
    except ClientError as e:
        return {
            "error": "Erro ao obter detalhes da imagem do S3",
            "message": str(e)
        }

    # Constrói a URL para acessar a imagem diretamente do S3
    url_to_image = f"https://{bucket_name}.s3.amazonaws.com/{image_key}"
    formatted_creation_date = response["LastModified"].strftime("%d-%m-%Y %H:%M:%S")

    return {
        "url_to_image": url_to_image,
        "created_image": formatted_creation_date
    }

def detect_face_emotions(bucket_name: str, image_name: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Detecta emoções faciais em uma imagem armazenada no S3 usando o Amazon Rekognition.

    Args:
        bucket_name (str): O nome do bucket S3.
        image_name (str): O nome da imagem no S3.

    Returns:
        dict: Dados das emoções detectadas ou mensagem de erro.
    """
    rekognition = boto3.client('rekognition')
    image_key = f"{FOLDER_NAME}/{image_name}"  # Constrói o caminho da imagem com base na pasta

    try:
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}},
            Attributes=['ALL']
        )

        if response['FaceDetails']:
            emotions = response['FaceDetails'][0]['Emotions']
            return {"Emotions": emotions}
        else:
            return {"error": "Nenhuma face detectada na imagem"}

    except ClientError as e:
        return {"error": "Erro ao detectar emoções faciais", "message": str(e)}
