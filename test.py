import os
from dotenv import load_dotenv
from azure.data.tables import TableServiceClient

print("🚀 Script started")

# Load .env file
print("🔍 Loading .env...")
load_dotenv()
print("✅ .env loaded")

# Get values from environment
conn_str = os.getenv("AZURE_TABLE_CONN_STRING")
table_name = os.getenv("DRYRUN_TABLE_NAME", "DryRunJobTracking")

if not conn_str:
    print("❌ AZURE_TABLE_CONN_STRING not found in .env")
    exit(1)

print(f"🔄 Connecting to Azure Table Storage with table '{table_name}'...")

try:
    table_service = TableServiceClient.from_connection_string(conn_str)

    # ✅ Create table if it doesn't exist using TableServiceClient
    table_service.create_table_if_not_exists(table_name)

    # Now get the table client to perform operations
    table_client = table_service.get_table_client(table_name)
    print(f"✅ Successfully connected and verified table: {table_name}")

    # Optional: test write
    from uuid import uuid4
    from datetime import datetime

    test_entity = {
        "PartitionKey": "test",
        "RowKey": str(uuid4()),
        "message": "Hello from test script",
        "createdAt": datetime.utcnow().isoformat()
    }

    table_client.create_entity(test_entity)
    print("✅ Successfully inserted test entity.")

except Exception as e:
    print("❌ Failed to connect or create table or insert entity.")
    print(str(e))
