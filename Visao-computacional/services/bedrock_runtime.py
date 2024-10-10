import json
import boto3
import logging
import os
from botocore.exceptions import ClientError

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa a sessão e o cliente Bedrock Runtime
session = boto3.Session(region_name='us-east-1')  # Certifique-se de usar a região correta
bedrock_client = session.client('bedrock-runtime')

# Exemplo de invocação do modelo Titan Text G1 - Express
model_id = 'amazon.titan-text-express-v1'  # ID correto do modelo Titan Text G1 - Express
input_text = "Um exemplo de descrição para gerar um texto."  # Texto de exemplo

# Estrutura do corpo da requisição para geração de texto
native_request = {
    "inputText": input_text,
    "textGenerationConfig": {
        "maxTokenCount": 500,  # Ajuste o número máximo de tokens gerados
        "temperature": 0.7,    # Controla a aleatoriedade das respostas (0.0 para determinístico)
        "topP": 0.9,           # Top-p sampling para limitar a probabilidade cumulativa
    },
}

logger.info(f"Iniciando a invocação do modelo: {model_id} com texto: {input_text}")

try:
    # Invocação do modelo de geração de texto
    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=json.dumps(native_request),
        contentType='application/json'
    )

    # Processando a resposta
    model_response = json.loads(response['body'].read())
    logger.info(f"Resposta do modelo: {model_response}")
    print(f"Texto gerado: {model_response}")

except ClientError as e:
    logger.error(f"Erro ao invocar o modelo: {e}")
    print({"error": "Erro ao invocar o modelo no Bedrock", "message": str(e)})

except Exception as e:
    logger.error(f"Erro inesperado: {e}")
    print({"error": "Erro inesperado ao invocar o modelo", "message": str(e)})
