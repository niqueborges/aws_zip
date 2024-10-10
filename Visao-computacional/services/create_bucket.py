import sys
import os
import boto3
import json
from botocore.exceptions import ClientError
import importlib
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

print("Diretório atual:", os.getcwd())

# Adiciona o caminho do diretório pai ao sys.path (caso necessário)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa o módulo para adicionar variáveis de ambiente (se existir)
try:
    add_env_var = importlib.import_module("utils.check_env").add_env_var
except ModuleNotFoundError as e:
    print(f"Erro ao importar o módulo: {e}")
    add_env_var = None

def create_bucket_if_not_exists(bucket_name):
    """Cria o bucket no S3 caso ele não exista."""
    s3 = boto3.client('s3')

    try:
        # Verifica se o bucket já existe
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} já existe.")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            try:
                # Cria o bucket
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': boto3.session.Session().region_name}
                )
                print(f"Bucket {bucket_name} criado.")

                # Desabilita o bloqueio de ACLs públicas
                s3.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': False,
                        'IgnorePublicAcls': False,
                        'BlockPublicPolicy': False,
                        'RestrictPublicBuckets': False
                    }
                )

                # Define uma política de bucket para permitir acesso público
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        },
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": "s3:PutObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        }
                    ]
                }
                s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))
                print(f"Política do bucket {bucket_name} aplicada com sucesso.")
                return True
            except ClientError as e:
                print(f"Erro ao criar o bucket: {e}")
                return False
        else:
            print(f"Erro ao verificar o bucket: {e}")
            return False

def upload_image_to_s3(bucket_name, file_name, s3_key):
    """Faz o upload de uma imagem para o S3."""
    s3 = boto3.client('s3')
    try:
        # Faz o upload da imagem
        s3.upload_file(file_name, bucket_name, s3_key)
        print(f"Imagem {file_name} enviada com sucesso para {s3_key} no bucket {bucket_name}.")
    except ClientError as e:
        print(f"Erro ao fazer upload da imagem: {e}")

if __name__ == "__main__":
    # Nome do bucket a partir do arquivo .env
    bucket_name = os.getenv('BUCKET_NAME')

    # Caminho da pasta que contém as imagens
    folder_path = 'imagens_bucket'

    # Lista de imagens a partir do arquivo .env
    image_files = [
        os.getenv('IMAGE_NAME_1'),
        os.getenv('IMAGE_NAME_2'),
        os.getenv('IMAGE_NAME_3'),
        os.getenv('IMAGE_NAME_4')
    ]

    # Cria o bucket se ele não existir
    if create_bucket_if_not_exists(bucket_name):
        # Faz o upload de cada imagem na lista
        for file_name in image_files:
            if file_name:  # Verifica se o nome do arquivo não é None
                # Cria o caminho completo para a imagem
                full_file_path = os.path.join(folder_path, file_name)
                s3_key = f"{os.getenv('FOLDER_NAME')}/{file_name}"  # Define a chave no S3 para simular a pasta
                upload_image_to_s3(bucket_name, full_file_path, s3_key)

        # Adiciona as variáveis de ambiente (se o método estiver disponível)
        if add_env_var:
            add_env_var({
                "BUCKET_NAME": bucket_name,
                "VISION_S3_DIR": os.getenv('FOLDER_NAME')  # Diretório para o projeto
            })
            print("Variáveis de ambiente adicionadas com sucesso.")
