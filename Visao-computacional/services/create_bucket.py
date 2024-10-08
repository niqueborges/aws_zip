import sys
import os
import boto3
import json
from botocore.exceptions import ClientError
import importlib

# Adiciona o caminho do diretório pai ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa o módulo para adicionar variáveis de ambiente
try:
    add_env_var = importlib.import_module("utils.check_env").add_env_var
except ModuleNotFoundError as e:
    print(f"Erro ao importar o módulo: {e}")
    sys.exit(1)

def create_bucket(bucket_name):
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

    # Adiciona informações ao .env se o bucket foi criado com sucesso
    add_env_var({
        "BUCKET_NAME": bucket_name, 
        "VISION_S3_DIR": "myphotos"  # Diretório para o projeto
    })
    print(f"Variáveis de ambiente adicionadas com sucesso.")

if __name__ == "__main__":
    create_bucket("photogrupo3v2")
