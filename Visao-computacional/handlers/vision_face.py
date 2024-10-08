import os
import json
import logging
import sys
from botocore.exceptions import ClientError

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adiciona o caminho do diretório visao-computacional ao sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

from services.bedrock_runtime import invoke_bedrock_model
from services.get_image import get_image_details, detect_face_emotions

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
    return len(errors) == 0, errors

def v1_vision(event, context):
    """
    Função para detectar emoções faciais em uma imagem armazenada no S3
    e utiliza o Bedrock para processar a imagem.

    Args:
        event (dict): Dados do evento que disparou a função.
        context (Any): Contexto de execução da função.

    Returns:
        dict: Resposta em formato JSON com os detalhes da imagem, emoções detectadas ou mensagem de erro.
    """
    try:
        body = json.loads(event.get("body", "{}"))  # Carrega o corpo da requisição
    except json.JSONDecodeError:
        logger.error("JSON inválido no corpo da requisição.")
        return {"statusCode": 400, "body": json.dumps({"error": "JSON inválido"})}

    # Valida os campos obrigatórios
    is_valid, errors = validate_input(body)
    if not is_valid:
        logger.error("Erro de validação: %s", errors)
        return {"statusCode": 400, "body": json.dumps({"error": "Erro de validação", "details": errors})}

    bucket_name = body["bucket"]
    image_path = f"myphotos/{body['imageName']}"  # Inclui a pasta 'myphotos' no caminho

    # Obtém detalhes da imagem
    s3_image_details = get_image_details(bucket_name, image_path)
    if "error" in s3_image_details:
        logger.error("Erro ao obter detalhes da imagem: %s", s3_image_details["error"])
        return {"statusCode": 500, "body": json.dumps(s3_image_details)}

    # Detecta emoções na imagem
    face_data = detect_face_emotions(bucket_name, image_path)
    if "error" in face_data:
        logger.error("Erro ao detectar emoções: %s", face_data["error"])
        return {"statusCode": 500, "body": json.dumps(face_data)}

    # Integração com AWS Bedrock
    text_input = f"Análise da imagem: {body['imageName']}"
    bedrock_response = invoke_bedrock_model(model_id="amazon.titan-image-generator-v2:0", text=text_input)
    
    if "error" in bedrock_response:
        logger.error("Erro ao processar a imagem com Bedrock: %s", bedrock_response["error"])
        return {"statusCode": 500, "body": json.dumps(bedrock_response)}

    # Combina todos os dados para a resposta final
    response_body = {**s3_image_details, **face_data, "bedrock_analysis": bedrock_response}

    logger.info("Processamento concluído com sucesso.")
    return {
        "statusCode": 200,
        "body": json.dumps(response_body, indent=4, ensure_ascii=True)
    }
