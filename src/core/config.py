import os

from dotenv import load_dotenv

load_dotenv('../../.env')

class Config:

    PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY")
    PIXABAY_IMAGES_URL = os.environ.get("PIXABAY_IMAGES_URL") 
    PIXABAY_VIDEOS_URL = os.environ.get("PIXABAY_VIDEOS_URL")
    OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT")

    LOGGER_FORMATTER_FORMAT = '%(levelname)s at %(asctime)s | %(filename)s | %(funcName)s >> %(message)s'