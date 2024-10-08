import os
from pathlib import Path
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, EndpointConnectionError, ClientError

class AWSConnectionManager:
    """Conexão com AWS utilizando boto3."""

    def __init__(self):
        self.credentials = None
        self.s3_client = None

    @staticmethod
    def clean_terminal():
        """Limpa o terminal: Windows/Linux."""
        os.system('cls' if os.name == 'nt' else 'clear')

    @staticmethod
    def aws_credentials_file_path() -> Path:
        """Caminho das credenciais da AWS."""
        return Path.home() / '.aws' / 'credentials'

    def load_credentials_from_file(self):
        """Carrega as credenciais do arquivo, se disponíveis."""
        credentials_path = self.aws_credentials_file_path()

        if credentials_path.exists():
            try:
                # O boto3 automaticamente carrega as credenciais do arquivo
                session = boto3.Session()
                credentials = session.get_credentials().get_frozen_credentials()

                self.credentials = {
                    'aws_access_key_id': credentials.access_key,
                    'aws_secret_access_key': credentials.secret_key,
                    'aws_session_token': credentials.token
                }
            except Exception as e:
                print(f"Erro ao carregar credenciais do arquivo: {e}")
                self.credentials = None
        else:
            print("Arquivo de credenciais não encontrado.")

    def ask_for_credentials(self):
        """Solicita ao usuário as credenciais AWS."""
        self.clean_terminal()

        self.credentials = {
            'aws_access_key_id': input("Insira sua AWS Access Key: "),
            'aws_secret_access_key': input("Insira sua AWS Secret Key: "),
            'aws_session_token': input("Insira seu AWS Session Token: ")
        }

    def save_credentials(self):
        """Salva as credenciais AWS no diretório .aws."""
        credentials_path = self.aws_credentials_file_path()

        # Verifica se o diretório .aws existe, se não, cria
        aws_dir = credentials_path.parent
        aws_dir.mkdir(parents=True, exist_ok=True)

        credentials_content = f"""
[default]
aws_access_key_id = {self.credentials['aws_access_key_id']}
aws_secret_access_key = {self.credentials['aws_secret_access_key']}
aws_session_token = {self.credentials['aws_session_token']}
"""

        try:
            with open(credentials_path, 'w') as file:
                file.write(credentials_content)
            print("Credenciais salvas com sucesso.")
        except Exception as e:
            print(f"Erro ao salvar credenciais: {e}")

    def create_s3_client(self):
        """Cria um cliente S3 usando as credenciais fornecidas ou as padrão."""
        try:
            if self.credentials:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.credentials['aws_access_key_id'],
                    aws_secret_access_key=self.credentials['aws_secret_access_key'],
                    aws_session_token=self.credentials['aws_session_token']
                )
            else:
                self.s3_client = boto3.client('s3')  # Usar credenciais padrão se disponíveis
        except Exception as e:
            print(f"Erro ao criar cliente S3: {e}")

    def check_aws_connection(self) -> bool:
        """Verifica a conexão com AWS S3."""
        if not self.s3_client:
            print("Cliente S3 não está inicializado.")
            return False
        
        try:
            self.s3_client.list_buckets()  # Lista os buckets para verificar a conexão
            print("Conexão com AWS bem-sucedida!")
            return True
        except NoCredentialsError:
            print("Credenciais AWS não encontradas.")
        except PartialCredentialsError:
            print("Credenciais AWS incompletas.")
        except EndpointConnectionError:
            print("Não foi possível conectar ao endpoint da AWS.")
        except ClientError as e:
            print(f"Erro ao conectar na AWS: {e}")

        return False

    def run(self):
        """Executa a conexão com a AWS, solicitando credenciais se necessário."""
        self.load_credentials_from_file()

        while True:
            if not self.s3_client:
                self.create_s3_client()

            if self.check_aws_connection():
                break  # Sai do loop quando a conexão for bem-sucedida
            
            print("Solicitando novas credenciais...")
            self.ask_for_credentials()
            self.save_credentials()
            self.create_s3_client()

# Execução
if __name__ == "__main__":
    manager = AWSConnectionManager()
    manager.run()
