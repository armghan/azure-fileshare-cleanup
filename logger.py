import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load .env settings (LOG_LEVEL, LOG_FILE)
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "cleanup.log")
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))  # 5MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 3))

def get_logger(name: str = "azure_cleanup") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Avoid adding handlers multiple times

    logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    # File Handler with rotation
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT)
    file_handler.setFormatter(formatter)

    # Console Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
