import os

from dotenv import load_dotenv

load_dotenv('../../.env')

class Config:

    MEDIA_FILE_DIR = os.environ.get("MEDIA_FILE_DIR")
    OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT")

    LOGGER_FORMATTER_FORMAT = '%(levelname)s at %(asctime)s | %(filename)s | %(funcName)s >> %(message)s'