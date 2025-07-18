import os
from dotenv import load_dotenv
load_dotenv()

# Static Configs
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", 30))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
SCHEDULE_POLL_INTERVAL_MINUTES = int(os.getenv("SCHEDULE_POLL_INTERVAL_MINUTES", 120))

# Azure Table Configs
AZURE_TABLE_CONN_STRING = os.getenv("AZURE_TABLE_CONN_STRING")
CLEANUP_TABLE_NAME = os.getenv("CLEANUP_TABLE_NAME", "CleanupJobTracking")
DRYRUN_TABLE_NAME = os.getenv("DRYRUN_TABLE_NAME", "DryRunJobTracking")
PVC_METADATA_TABLE = os.getenv("PVC_METADATA_TABLE", "PVCMetadata")
STORAGE_ACCOUNTS_TABLE = os.getenv("STORAGE_ACCOUNTS_TABLE", "StorageAccounts")

# Optional: Fallback for direct manual cleanup APIs
AZURE_FILES_CONN_STRING = os.getenv("AZURE_FILES_CONN_STRING", "")
