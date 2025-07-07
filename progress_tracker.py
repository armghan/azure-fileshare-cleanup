from uuid import uuid4
from azure.data.tables import TableServiceClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import logging

load_dotenv()

AZURE_TABLE_CONN_STRING = os.getenv("AZURE_TABLE_CONN_STRING")
CLEANUP_TABLE_NAME = os.getenv("CLEANUP_TABLE_NAME", "CleanupJobs")

logger = logging.getLogger(__name__)

# Initialize Table Service and create table if it doesn't exist
try:
    table_service = TableServiceClient.from_connection_string(AZURE_TABLE_CONN_STRING)
    table_service.create_table_if_not_exists(CLEANUP_TABLE_NAME)
    table_client = table_service.get_table_client(CLEANUP_TABLE_NAME)
    logger.info(f"✅ Connected to cleanup table: {CLEANUP_TABLE_NAME}")
except Exception as e:
    logger.error(f"❌ Could not connect to or create table '{CLEANUP_TABLE_NAME}'", exc_info=True)
    table_client = None

def create_job():
    job_id = str(uuid4())
    entity = {
        "PartitionKey": "cleanup",
        "RowKey": job_id,
        "status": "pending",
        "progress": 0,
        "deleted": 0,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

    if table_client:
        try:
            table_client.create_entity(entity)
        except Exception as e:
            logger.error(f"❌ Failed to create cleanup job {job_id}", exc_info=True)

    return job_id

def update_progress(job_id, status=None, progress=None, deleted=None):
    if not table_client:
        return

    try:
        entity = table_client.get_entity(partition_key="cleanup", row_key=job_id)
        if status:
            entity["status"] = status
        if progress is not None:
            entity["progress"] = progress
        if deleted is not None:
            entity["deleted"] = deleted
        entity["updatedAt"] = datetime.now(timezone.utc).isoformat()
        table_client.update_entity(entity, mode="merge")
    except Exception as e:
        logger.error(f"❌ Failed to update cleanup job {job_id}", exc_info=True)

def get_progress(job_id):
    if not table_client:
        return {"error": "No table client available"}

    try:
        entity = table_client.get_entity(partition_key="cleanup", row_key=job_id)
        return {
            "progress": entity.get("progress", 0),
            "deleted": entity.get("deleted", 0),
            "status": entity.get("status", "unknown")
        }
    except Exception:
        logger.warning(f"⚠️ Cleanup job not found: {job_id}")
        return {"error": "Invalid job ID"}
