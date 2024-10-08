import json
import boto3
from botocore.exceptions import ClientError

# Mensagens constantes
HEALTH_MESSAGE = "Go Serverless v3.0! Your function executed successfully!"
VERSION_1_MESSAGE = "VISION API version 1."
VERSION_2_MESSAGE = "VISION API version 2."

# Inicializa clientes para S3 e Bedrock
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime')

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

def process_image(event, context):
    """Process an image from S3, analyze it using Bedrock and return results."""
    # Extrai o nome do bucket e a imagem do evento
    bucket_name = event.get('bucket')
    image_name = event.get('imageName')

    if not bucket_name or not image_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing bucket or imageName"})
        }

    # Tenta obter a imagem do S3
    try:
        image_object = s3_client.get_object(Bucket=bucket_name, Key=image_name)
        image_content = image_object['Body'].read()  # 'image_content' não está sendo utilizado
    except ClientError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to retrieve image from S3", "message": str(e)})
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
                "url_to_image": f"https://{bucket_name}.s3.amazonaws.com/{image_name}",
                "bedrock_output": bedrock_output
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Failed to process the image with Bedrock", "message": str(e)})
        }
