import logging

from src.core.config import Config


def get_logger(name, level = logging.DEBUG):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(Config.LOGGER_FORMATTER_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger