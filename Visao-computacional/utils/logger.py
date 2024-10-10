import logging

def log_to_cloudwatch(message):
    logging.basicConfig(level=logging.INFO)
    logging.info(message)