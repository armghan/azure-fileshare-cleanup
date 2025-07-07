from uuid import uuid4
from azure.data.tables import TableServiceClient
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

AZURE_TABLE_CONN_STRING = os.getenv("AZURE_TABLE_CONN_STRING")
DRYRUN_TABLE_NAME = os.getenv("DRYRUN_TABLE_NAME", "DryRunJobTracking")

logger = logging.getLogger(__name__)

# Initialize Table Client
try:
    table_service = TableServiceClient.from_connection_string(AZURE_TABLE_CONN_STRING)
    table_client = table_service.get_table_client(DRYRUN_TABLE_NAME)
    try:
        table_service.create_table(DRYRUN_TABLE_NAME)
        logger.info(f"✅ Table '{DRYRUN_TABLE_NAME}' created.")
    except Exception:
        logger.info(f"ℹ️ Table '{DRYRUN_TABLE_NAME}' already exists.")
except Exception as e:
    logger.error(f"❌ Could not connect or create table '{DRYRUN_TABLE_NAME}'", exc_info=True)
    table_client = None

def create_dryrun_job():
    job_id = str(uuid4())
    entity = {
        "PartitionKey": "dryrun",
        "RowKey": job_id,
        "status": "pending",
        "progress": 0,
        "scanned": 0,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

    if table_client:
        try:
            table_client.create_entity(entity)
        except Exception as e:
            logger.error(f"❌ Failed to create dry-run job {job_id}", exc_info=True)

    return job_id

def update_dryrun_progress(job_id, status=None, progress=None, scanned=None):
    if not table_client:
        return

    try:
        entity = table_client.get_entity(partition_key="dryrun", row_key=job_id)
        if status:
            entity["status"] = status
        if progress is not None:
            entity["progress"] = progress
        if scanned is not None:
            entity["scanned"] = scanned
        entity["updatedAt"] = datetime.now(timezone.utc).isoformat()
        table_client.update_entity(entity, mode="replace")  # Use 'replace' instead of 'merge'
        logger.debug(f"✅ Updated dry-run job {job_id}: status={status}, progress={progress}, scanned={scanned}")
    except Exception as e:
        logger.error(f"❌ Failed to update dry-run job {job_id}", exc_info=True)

def get_dryrun_progress(job_id):
    if not table_client:
        return {"error": "No table client available"}

    try:
        entity = table_client.get_entity(partition_key="dryrun", row_key=job_id)
        return {
            "progress": entity.get("progress", 0),
            "scanned": entity.get("scanned", 0),
            "status": entity.get("status", "unknown")
        }
    except Exception as e:
        logger.warning(f"⚠️ Dry-run job not found: {job_id}")
        return {"error": "Invalid dry-run job ID"}
