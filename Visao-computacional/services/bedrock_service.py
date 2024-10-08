import boto3
import json
import logging
from botocore.exceptions import ClientError

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def invoke_bedrock_model(
    model_id: str,
    text: str,
    cfg_scale: int = 8,
    seed: int = 0,
    quality: str = "standard",
    width: int = 1024,
    height: int = 1024,
    number_of_images: int = 3
) -> dict:
    """
    Invoca um modelo no AWS Bedrock para gerar imagens a partir de texto.

    Args:
        model_id (str): ID do modelo a ser invocado.
        text (str): Texto que será usado para a geração da imagem.
        cfg_scale (int): Escala de configuração para o modelo.
        seed (int): Semente para a geração aleatória.
        quality (str): Qualidade da imagem gerada.
        width (int): Largura da imagem gerada.
        height (int): Altura da imagem gerada.
        number_of_images (int): Número de imagens a serem geradas.

    Returns:
        dict: Resultado da invocação do modelo, incluindo imagens geradas ou mensagens de erro.
    """
    if not model_id or not text:
        return {"error": "model_id e text são obrigatórios."}
    
    bedrock_client = boto3.client('bedrock')

    request_body = {
        "textToImageParams": {"text": text},
        "taskType": "TEXT_IMAGE",
        "imageGenerationConfig": {
            "cfgScale": cfg_scale,
            "seed": seed,
            "quality": quality,
            "width": width,
            "height": height,
            "numberOfImages": number_of_images
        }
    }

    try:
        logger.info(f"Iniciando a invocação do modelo: {model_id} com texto: {text}")
        response = bedrock_client.invoke_model(
            ModelId=model_id,
            ContentType="application/json",
            Body=json.dumps(request_body)
        )

        return json.loads(response['Body'].read())
    
    except ClientError as e:
        logger.error(f"Erro ao invocar o modelo: {e}")
        return {"error": "Erro ao invocar o modelo no Bedrock", "message": str(e)}
