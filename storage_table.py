import os
from azure.data.tables import TableServiceClient

# Use a single environment variable for all metadata access
AZURE_TABLE_CONN_STRING = os.getenv("AZURE_TABLE_CONN_STRING")

def get_table_client(table_name: str):
    if not AZURE_TABLE_CONN_STRING:
        raise ValueError("AZURE_TABLE_CONN_STRING environment variable not set.")
    service = TableServiceClient.from_connection_string(AZURE_TABLE_CONN_STRING)
    return service.get_table_client(table_name=table_name)

def get_pvc_metadata():
    table = get_table_client("PVCMetadata")
    return list(table.list_entities())

def get_storage_connection_string(storage_account_name: str) -> str:
    table = get_table_client("StorageAccounts")
    entity = table.get_entity(partition_key="default", row_key=storage_account_name)
    return entity["connection_string"]
