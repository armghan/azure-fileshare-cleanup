from azure.storage.fileshare import ShareServiceClient
from datetime import datetime, timedelta, timezone
from config import AZURE_FILES_CONN_STRING
from config import RETENTION_DAYS
from dryrun_tracker import update_dryrun_progress
from audit_logger import is_excluded, is_date_dir, log_dryrun_candidate
import logging

logger = logging.getLogger(__name__)

def dryrun_file_share(job_id, share_name):
    try:
        client = ShareServiceClient.from_connection_string(AZURE_FILES_CONN_STRING)
        share_client = client.get_share_client(share_name)
        now = datetime.now(timezone.utc)
        processed = 0

        def walk(dir_client, path=""):
            nonlocal processed
            items = list(dir_client.list_directories_and_files())

            for item in items:
                full_path = f"{path}/{item['name']}".strip("/")

                if is_excluded(full_path):
                    continue

                if item["is_directory"]:
                    if is_date_dir(item["name"]):
                        log_dryrun_candidate(share_name, full_path, "Directory")
                        continue
                    walk(share_client.get_directory_client(full_path), full_path)
                else:
                    file_client = share_client.get_file_client(full_path)
                    props = file_client.get_file_properties()
                    processed += 1
                    if props["last_modified"] < now - timedelta(days=RETENTION_DAYS):
                        log_dryrun_candidate(share_name, full_path, "File")

                if processed % 10 == 0:
                    update_dryrun_progress(job_id, progress=(processed % 100), scanned=processed)

        walk(share_client.get_directory_client(""))
        update_dryrun_progress(job_id, status="completed", progress=100, scanned=processed)
    except Exception as e:
        logger.error(f"DryRun failed for job {job_id}", exc_info=True)
        update_dryrun_progress(job_id, status=f"failed: {str(e)}")
