import json
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Union
import os

# Mensagens constantes
HEALTH_MESSAGE = "Go Serverless v3.0! Your function executed successfully!"
VERSION_1_MESSAGE = "VISION API version 1."
VERSION_2_MESSAGE = "VISION API version 2."

import boto3

# Inicializa a sessão boto3 com a região apropriada
session = boto3.Session(region_name='us-east-1')  # Ajuste a região conforme necessário

# Cria clientes para Rekognition e Bedrock
rekognition = session.client('rekognition')
bedrock = session.client('bedrock-runtime')  # Certifique-se de que este serviço é suportado

# Variável de ambiente para o nome da pasta
FOLDER_NAME = os.getenv("FOLDER_NAME", "default_folder")  # Substitua "default_folder" pelo valor padrão desejado

def health(event, context):
    """Health check endpoint."""
    body = {
        "message": HEALTH_MESSAGE,
        "input": event,
    }

    return {
        "statusCode": 200,
        "body": json.dumps(body)
    }

def v1_description(event, context):
    """Description for version 1 of the VISION API."""
    return {
        "statusCode": 200,
        "body": json.dumps({"message": VERSION_1_MESSAGE})
    }

def v2_description(event, context):
    """Description for version 2 of the VISION API."""
    return {
        "statusCode": 200,
        "body": json.dumps({"message": VERSION_2_MESSAGE})
    }

def get_image_details(bucket_name: str, image_name: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Obtém os detalhes de uma imagem armazenada no S3.
    """
    image_key = f"{FOLDER_NAME}/{image_name}"  # Constrói o caminho da imagem com base na pasta
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=image_key)
        url_to_image = f"https://{bucket_name}.s3.amazonaws.com/{image_key}"
        formatted_creation_date = response["LastModified"].strftime("%d-%m-%Y %H:%M:%S")
        return {
            "url_to_image": url_to_image,
            "created_image": formatted_creation_date
        }
    except ClientError as e:
        return {"error": "Erro ao obter detalhes da imagem do S3", "message": str(e)}

def detect_face_emotions(bucket_name: str, image_name: str) -> Union[Dict[str, Any], Dict[str, str]]:
    """
    Detecta emoções faciais em uma imagem armazenada no S3 usando o Amazon Rekognition.
    """
    rekognition = boto3.client('rekognition')
    image_key = f"{FOLDER_NAME}/{image_name}"  # Constrói o caminho da imagem com base na pasta
    try:
        response = rekognition.detect_faces(
            Image={'S3Object': {'Bucket': bucket_name, 'Name': image_key}},
            Attributes=['ALL']
        )
        if response['FaceDetails']:
            return {"Emotions": response['FaceDetails'][0]['Emotions']}
        else:
            return {"error": "Nenhuma face detectada na imagem"}
    except ClientError as e:
        return {"error": "Erro ao detectar emoções faciais", "message": str(e)}

def process_image(event, context):
    """Processa uma imagem do S3, analisa-a usando Bedrock e retorna resultados."""
    bucket_name = event.get('bucket')
    image_name = event.get('imageName')

    # Valida os parâmetros de entrada
    if not bucket_name or not image_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing bucket or imageName"})
        }

    # Obtém os detalhes da imagem
    image_details = get_image_details(bucket_name, image_name)
    if "error" in image_details:
        return {
            "statusCode": 500,
            "body": json.dumps(image_details)
        }

    # Detecta emoções na imagem
    emotions_data = detect_face_emotions(bucket_name, image_name)
    if "error" in emotions_data:
        return {
            "statusCode": 500,
            "body": json.dumps(emotions_data)
        }

    # Processa a imagem usando Bedrock
    prompt = "Descreva a imagem a seguir."
    native_request = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 500,
            "temperature": 0.7,
            "topP": 0.9,
        },
    }

    try:
        # Chama o Bedrock para gerar informações
        response = bedrock_client.invoke_model(
            modelId="amazon.titan-text-express-v1",  # ID do modelo
            body=json.dumps(native_request),
        )

        # Decodifica a resposta
        model_response = json.loads(response["body"].read())
        bedrock_output = model_response["results"][0]["outputText"]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "url_to_image": image_details["url_to_image"],
                "created_image": image_details["created_image"],
                "bedrock_output": bedrock_output,
                "emotions": emotions_data["Emotions"]
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to process the image with Bedrock", "message": str(e)})
        }
