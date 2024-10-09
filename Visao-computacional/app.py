import boto3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Flask!"

def list_s3_buckets():
    """Função para listar os buckets do S3."""
    # Inicializa uma sessão usando o Amazon S3
    s3 = boto3.client('s3')

    # Chama o S3 para listar os buckets atuais
    response = s3.list_buckets()

    # Obtém uma lista de todos os nomes dos buckets da resposta
    buckets = [bucket['Name'] for bucket in response['Buckets']]

    # Retorna a lista de buckets
    return buckets

if __name__ == "__main__":
    # Executa o servidor Flask em modo de desenvolvimento
    app.run(debug=True)
