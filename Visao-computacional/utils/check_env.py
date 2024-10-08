import os

def add_env_var(variables: dict):
    env_file = '.env'
    
    try:
        # Lê o conteúdo existente do .env ou inicializa uma lista vazia
        lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r') as file:
                lines = file.readlines()

        # Para cada variável, verifica se já existe e adiciona se não
        new_lines = [
            f"{key}={value}\n" for key, value in variables.items()
            if not any(line.startswith(f"{key}=") for line in lines)
        ]

        # Adiciona as novas variáveis ao final do arquivo
        if new_lines:
            with open(env_file, 'a') as file:
                file.writelines(new_lines)

    except IOError as e:
        print(f"Erro ao acessar o arquivo .env: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# Exemplo de uso:
add_env_var({
    "BUCKET_NAME": "vision-project-bucket",
    "IMAGE_S3_DIR": "images",
    "API_KEY": "your_api_key_here",
    "ENDPOINT_URL": "https://your-endpoint-url.com",
    "VISION_S3_DIR": "myphotos"
})
