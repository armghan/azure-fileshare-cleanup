import os
from dotenv import load_dotenv
load_dotenv()

AZURE_FILES_CONN_STRING = os.getenv("AZURE_FILES_CONN_STRING")
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", 30))