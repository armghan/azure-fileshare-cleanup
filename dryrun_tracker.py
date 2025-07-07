from uuid import uuid4
from azure.data.tables import TableServiceClient, TableEntity
from datetime import datetime
import os
from dotenv import load_dotenv
import logging

load_dotenv()

AZURE_TABLE_CONN_STRING = os.getenv("AZURE_TABLE_CONN_STRING")
DRYRUN_TABLE_NAME = os.getenv("DRYRUN_TABLE_NAME", "DryRunJobs")

logger = logging.getLogger(__name__)

# Init Table Client
try:
    table_service = TableServiceClient.from_connection_string(AZURE_TABLE_CONN_STRING)
    table_client = table_service.get_table_client(DRYRUN_TABLE_NAME)
    table_client.create_table_if_not_exists()
except Exception as e:
    logger.error(f"❌ Could not connect or create table {DRYRUN_TABLE_NAME}", exc_info=True)
    table_client = None

def create_dryrun_job():
    job_id = str(uuid4())
    entity = {
        "PartitionKey": "dryrun",
        "RowKey": job_id,
        "status": "pending",
        "progress": 0,
        "processed": 0,
        "createdAt": datetime.utcnow().isoformat()
    }

    if table_client:
        table_client.create_entity(entity)
    return job_id

def update_dryrun_progress(job_id, status=None, progress=None, processed=None):
    if not table_client:
        return

    try:
        entity = table_client.get_entity(partition_key="dryrun", row_key=job_id)
        if status:
            entity["status"] = status
        if progress is not None:
            entity["progress"] = progress
        if processed is not None:
            entity["processed"] = processed
        entity["updatedAt"] = datetime.utcnow().isoformat()
        table_client.update_entity(entity, mode="Merge")
    except Exception as e:
        logger.error(f"❌ Failed to update dry-run job {job_id}", exc_info=True)

def get_dryrun_progress(job_id):
    if not table_client:
        return {"error": "No table client available"}

    try:
        entity = table_client.get_entity(partition_key="dryrun", row_key=job_id)
        return {
            "progress": entity.get("progress", 0),
            "processed": entity.get("processed", 0),
            "status": entity.get("status", "unknown")
        }
    except Exception as e:
        logger.warning(f"⚠️ Dry-run job not found: {job_id}")
        return {"error": "Invalid dry-run job ID"}
