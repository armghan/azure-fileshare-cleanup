import os
from dotenv import load_dotenv
load_dotenv()

AZURE_FILES_CONN_STRING = os.getenv("AZURE_FILES_CONN_STRING")
AZURE_AUDIT_CONN_STRING = os.getenv("AZURE_AUDIT_CONN_STRING")
AUDIT_TABLE_NAME = os.getenv("AUDIT_TABLE_NAME", "FileCleanupAudit")