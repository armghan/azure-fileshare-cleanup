from azure.storage.fileshare import ShareServiceClient
from datetime import datetime, timedelta, timezone
from config import AZURE_FILES_CONN_STRING, RETENTION_DAYS
from progress_tracker import update_progress
from audit_logger import is_excluded, is_date_dir
import logging

logger = logging.getLogger(__name__)

def cleanup_file_share(job_id, share_name):
    try:
        client = ShareServiceClient.from_connection_string(AZURE_FILES_CONN_STRING)
        share_client = client.get_share_client(share_name)
        now = datetime.now(timezone.utc)
        deleted = 0

        def walk(dir_client, path=""):
            nonlocal deleted
            items = list(dir_client.list_directories_and_files())

            for item in items:
                full_path = f"{path}/{item['name']}".strip("/")

                if is_excluded(full_path):
                    continue

                if item["is_directory"]:
                    if is_date_dir(item["name"], now):
                        try:
                            share_client.get_directory_client(full_path).delete_directory()
                            logger.info(f"[Cleanup] Deleted directory: {full_path}")
                            deleted += 1
                        except Exception as e:
                            logger.warning(f"[Cleanup] Failed to delete directory: {full_path} - {str(e)}")
                        continue
                    walk(share_client.get_directory_client(full_path), full_path)
                else:
                    file_client = share_client.get_file_client(full_path)
                    props = file_client.get_file_properties()
                    if props["last_modified"] < now - timedelta(days=RETENTION_DAYS):
                        try:
                            file_client.delete_file()
                            logger.info(f"[Cleanup] Deleted file: {full_path}")
                            deleted += 1
                        except Exception as e:
                            logger.warning(f"[Cleanup] Failed to delete file: {full_path} - {str(e)}")

                if deleted % 10 == 0:
                    update_progress(job_id, progress=(deleted % 100), deleted=deleted)

        walk(share_client.get_directory_client(""))
        update_progress(job_id, status="completed", progress=100, deleted=deleted)
    except Exception as e:
        logger.error(f"Cleanup failed for job {job_id}", exc_info=True)
        update_progress(job_id, status=f"failed: {str(e)}")
