from datetime import datetime
from azure.core.exceptions import ResourceNotFoundError
from storage_table import get_table_client
from logger import get_logger  # ✅ Reuse logger

logger = get_logger("progress_tracker")

def create_progress_entry(job_id: str, share_name: str, status: str):
    table_client = get_table_client("CleanupJobTracking")
    entity = {
        "PartitionKey": "cleanup",
        "RowKey": job_id,
        "share_name": share_name,
        "status": status,
        "processed": 0,
        "deleted": 0,
        "failed": 0,
        "last_update": datetime.utcnow().isoformat() + "Z",
        "message": ""
    }
    table_client.create_entity(entity=entity)
    logger.info(f"📝 Created tracking entry for job {job_id}")


def update_progress(
    job_id: str,
    status: str,
    processed: int = 0,
    deleted: int = 0,
    failed: int = 0,
    message: str = ""
):
    table_client = get_table_client("CleanupJobTracking")
    try:
        entity = table_client.get_entity(partition_key="cleanup", row_key=job_id)
        entity["status"] = status
        entity["processed"] = processed
        entity["deleted"] = deleted
        entity["failed"] = failed
        entity["last_update"] = datetime.utcnow().isoformat() + "Z"
        entity["message"] = message
        table_client.update_entity(mode="replace", entity=entity)
        logger.info(f"✅ Updated progress for job {job_id}")
    except ResourceNotFoundError:
        logger.error(f"❌ Failed to update cleanup job for {job_id} - not found in tracking table")
    except Exception as e:
        logger.exception(f"❌ Unexpected error updating progress for job {job_id}: {str(e)}")
