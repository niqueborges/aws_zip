import boto3
import logging
from botocore.exceptions import ClientError

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_face_emotions(bucket_name: str, image_name: str) -> dict:
    """
    Detecta emoções faciais em uma imagem armazenada no S3 usando o AWS Rekognition.

    Args:
        bucket_name (str): Nome do bucket S3 onde a imagem está armazenada.
        image_name (str): Nome da imagem no bucket S3 (incluindo o caminho da pasta).

    Returns:
        dict: Informações sobre as emoções detectadas nas faces ou mensagem de erro.
    """
    if not bucket_name or not image_name:
        logger.error("Nome do bucket ou da imagem não pode ser vazio.")
        return {"error": "Nome do bucket ou da imagem não pode ser vazio."}

    rekognition = boto3.client("rekognition")

    try:
        response = rekognition.detect_faces(
            Image={"S3Object": {"Bucket": bucket_name, "Name": image_name}},
            Attributes=["ALL"]
        )
        logger.info("Resposta do Rekognition recebida com sucesso.")
    except ClientError as e:
        logger.error("Erro ao chamar a API Rekognition: %s", e)
        return {"error": "Erro ao chamar a API Rekognition", "message": str(e)}

    if not response.get("FaceDetails"):
        logger.warning("Nenhuma face detectada na imagem.")
        return {"faces": [{"position": {}, "classified_emotion": None, "classified_emotion_confidence": None}]}

    return process_faces(response["FaceDetails"])

def process_faces(face_details):
    """Processa as faces detectadas e retorna as informações formatadas."""
    face_data = {"faces": []}

    for face in face_details:
        emotions = face.get("Emotions", [])
        max_emotion = max(emotions, key=lambda e: e["Confidence"], default={"Type": None, "Confidence": 0})
        
        face_info = {
            "position": face["BoundingBox"],
            "classified_emotion": max_emotion["Type"],
            "classified_emotion_confidence": max_emotion["Confidence"]
        }

        face_data["faces"].append(face_info)

    logger.info("Processamento concluído. Total de faces detectadas: %d", len(face_data["faces"]))
    return face_data
