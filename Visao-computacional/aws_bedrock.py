import boto3
import json

# Inicializar a sessão e o cliente Bedrock
session = boto3.Session(region_name='us-east-1')  # Certifique-se de usar a região correta
bedrock_client = session.client('bedrock')

# Tentar listar os modelos disponíveis e exibir a resposta completa
try:
    response = bedrock_client.list_foundation_models()
    print("Resposta completa da API:")
    print(json.dumps(response, indent=4, ensure_ascii=False))  # Exibe a resposta da API de forma legível

    # Verifique se a chave 'models' está presente na resposta
    if 'models' in response:
        for model in response['models']:
            print(f"Model ID: {model['modelId']}, Name: {model['modelName']}")
    else:
        print("A chave 'models' não está presente na resposta.")

except Exception as e:
    print(f"Erro ao listar os modelos: {str(e)}")

