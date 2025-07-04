from azure.data.tables import TableServiceClient
from config import AZURE_AUDIT_CONN_STRING, AUDIT_TABLE_NAME
from datetime import datetime
import uuid

EXCLUDED_DIRS = {"Outbound", "ConfigBackup", "certificates"}

table_service = TableServiceClient.from_connection_string(AZURE_AUDIT_CONN_STRING)
table_client = table_service.get_table_client(AUDIT_TABLE_NAME)

def ensure_table_exists():
    try:
        table_client.create_table()
    except:
        pass

ensure_table_exists()

def log_deletion(share_name, item_path, item_type):
    table_client.create_entity({
        "PartitionKey": share_name,
        "RowKey": str(uuid.uuid4()),
        "ItemPath": item_path,
        "ItemType": item_type,
        "DeletedAt": datetime.utcnow().isoformat()
    })

def is_excluded(path):
    return any(
        "config" in part.lower() or part in EXCLUDED_DIRS
        for part in path.strip("/").split("/")
    )

def is_date_dir(name):
    from datetime import datetime, timedelta
    import re
    try:
        parsed_date = datetime.strptime(name, "%Y-%m-%d")
        return parsed_date < datetime.utcnow() - timedelta(days=30)
    except ValueError:
        return False