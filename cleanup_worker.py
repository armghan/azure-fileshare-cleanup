from azure.storage.fileshare import ShareServiceClient
from datetime import datetime, timedelta, timezone
from config import AZURE_FILES_CONN_STRING
from progress_tracker import update_progress
from audit_logger import log_deletion, is_excluded, is_date_dir
from config import RETENTION_DAYS
import logging


logger = logging.getLogger(__name__)

def delete_directory_recursive(dir_client, share_name):
    try:
        for item in dir_client.list_directories_and_files():
            item_path = f"{dir_client.directory_path}/{item['name']}".strip("/")
            if item["is_directory"]:
                delete_directory_recursive(dir_client.get_subdirectory_client(item["name"]), share_name)
                dir_client.get_subdirectory_client(item["name"]).delete_directory()
                log_deletion(share_name, item_path, "Directory")
                logger.info(f"Deleted directory: {item_path}")
            else:
                dir_client.get_file_client(item["name"]).delete_file()
                log_deletion(share_name, item_path, "File")
                logger.info(f"Deleted file: {item_path}")
        dir_client.delete_directory()
        log_deletion(share_name, dir_client.directory_path, "Directory")
    except Exception as e:
        logger.error(f"Recursive deletion failed in {dir_client.directory_path}", exc_info=True)


def cleanup_file_share(job_id, share_name):
    try:
        client = ShareServiceClient.from_connection_string(AZURE_FILES_CONN_STRING)
        share_client = client.get_share_client(share_name)
        now = datetime.now(timezone.utc)
        deleted = 0
        processed = 0

        def walk(dir_client, path=""):
            nonlocal deleted, processed
            items = list(dir_client.list_directories_and_files())

            for item in items:
                full_path = f"{path}/{item['name']}".strip("/")

                if is_excluded(full_path):
                    continue

                if item["is_directory"]:
                    if is_date_dir(item["name"]):
                        delete_directory_recursive(share_client.get_directory_client(full_path), share_name)
                        deleted += 1
                        continue
                    walk(share_client.get_directory_client(full_path), full_path)
                else:
                    file_client = share_client.get_file_client(full_path)
                    props = file_client.get_file_properties()
                    processed += 1
                    if props["last_modified"] < now - timedelta(days=RETENTION_DAYS):
                        file_client.delete_file()
                        log_deletion(share_name, full_path, "File")
                        deleted += 1

                    if processed % 10 == 0:
                        update_progress(job_id, progress=(processed % 100), deleted=deleted)

        walk(share_client.get_directory_client(""))
        update_progress(job_id, status="completed", progress=100, deleted=deleted)
    except Exception as e:
        logger.error(f"Cleanup failed for job {job_id}", exc_info=True)
        update_progress(job_id, status=f"failed: {str(e)}")