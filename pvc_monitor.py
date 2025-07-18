import time
import uuid
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from storage_table import (
    get_pvc_metadata,
    get_storage_connection_string,
    get_table_client,
)
from cleanup_worker import cleanup_file_share
from progress_tracker import create_progress_entry
from logger import get_logger  # ✅ Reusable logger

# Load environment variables and initialize logger
load_dotenv()
logger = get_logger("pvc_monitor")

MONITOR_INTERVAL_HOURS = int(os.getenv("MONITOR_INTERVAL_HOURS", 1))

# Suppress verbose Azure SDK logs
import logging
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure").setLevel(logging.WARNING)

def schedule_cleanup(job_id, share_name, conn_str):
    try:
        create_progress_entry(job_id=job_id, share_name=share_name, status="Running")
    except Exception as e:
        if "EntityAlreadyExists" in str(e):
            logger.warning(f"⚠️ Tracking entry may already exist for {share_name}: {e}")
        else:
            logger.exception(f"❌ Failed to create tracking entry for {share_name}")
            return

    try:
        cleanup_file_share(job_id, conn_str, share_name)
    except Exception as e:
        logger.exception(f"❌ Cleanup failed for share {share_name}: {e}")

def monitor_and_schedule():
    logger.info("📡 PVC Monitor started")
    tracking_client = get_table_client("CleanupJobTracking")

    while True:
        try:
            pvc_entries = list(get_pvc_metadata())
            logger.info(f"🔍 Found {len(pvc_entries)} PVCs to check")

            for pvc in pvc_entries:
                share_name = pvc.get("share_name")
                storage_account = pvc.get("storage_account")
                schedule_hours = int(pvc.get("schedule_hours", 24))

                if not all([share_name, storage_account]):
                    logger.warning(f"⚠️ Invalid PVC entry: {pvc}")
                    continue

                job_id = share_name  # Use share_name as RowKey (idempotent tracking)

                try:
                    existing = tracking_client.get_entity("cleanup", job_id)
                    last_run = existing.get("last_update") or existing.get("start_time")
                    if last_run:
                        last_run_time = datetime.fromisoformat(last_run.rstrip("Z"))
                        next_run_time = last_run_time + timedelta(hours=schedule_hours)

                        if datetime.utcnow() < next_run_time:
                            logger.info(f"⏭ Skipping {share_name}, next run at {next_run_time.isoformat()}")
                            continue
                except Exception:
                    existing = None  # No entity found

                try:
                    conn_str = get_storage_connection_string(storage_account)
                    if not conn_str:
                        raise ValueError(f"No connection string found for storage account '{storage_account}'")

                    logger.info(f"🔐 Retrieved connection string for storage account: {storage_account}")
                    logger.info(f"⏱ Scheduling cleanup for share: {share_name}")

                    if not existing:
                        tracking_client.create_entity({
                            "PartitionKey": "cleanup",
                            "RowKey": job_id,
                            "share_name": share_name,
                            "start_time": datetime.utcnow().isoformat(),
                            "status": "Scheduled",
                            "message": "Scheduled via monitor"
                        })

                    schedule_cleanup(job_id, share_name, conn_str)

                except Exception as e:
                    logger.exception(f"❌ Could not schedule cleanup for {share_name} (StorageAccount: {storage_account})")

        except Exception as e:
            logger.exception(f"❌ PVC Monitor failed: {e}")

        logger.info(f"💤 Sleeping for {MONITOR_INTERVAL_HOURS}h...")
        time.sleep(MONITOR_INTERVAL_HOURS * 3600)

if __name__ == "__main__":
    monitor_and_schedule()
