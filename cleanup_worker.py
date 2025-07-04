from azure.storage.fileshare import ShareServiceClient
from datetime import datetime, timedelta
from config import AZURE_FILES_CONN_STRING
from progress_tracker import update_progress
from audit_logger import log_deletion, is_excluded, is_date_dir

def delete_directory_recursive(dir_client, share_name):
    for item in dir_client.list_directories_and_files():
        item_path = f"{dir_client.path_name}/{item['name']}".strip("/")
        if item["is_directory"]:
            delete_directory_recursive(dir_client._get_directory_client(item["name"]), share_name)
            dir_client._get_directory_client(item["name"]).delete_directory()
            log_deletion(share_name, item_path, "Directory")
        else:
            dir_client._get_file_client(item["name"]).delete_file()
            log_deletion(share_name, item_path, "File")
    dir_client.delete_directory()
    log_deletion(share_name, dir_client.path_name, "Directory")

def cleanup_file_share(job_id, share_name):
    try:
        client = ShareServiceClient.from_connection_string(AZURE_FILES_CONN_STRING)
        share_client = client.get_share_client(share_name)
        now = datetime.utcnow()
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
                    if props["last_modified"] < now - timedelta(days=30):
                        file_client.delete_file()
                        log_deletion(share_name, full_path, "File")
                        deleted += 1

                    if processed % 10 == 0:
                        update_progress(job_id, progress=(processed % 100), deleted=deleted)

        walk(share_client.get_directory_client(""))
        update_progress(job_id, status="completed", progress=100, deleted=deleted)
    except Exception as e:
        update_progress(job_id, status=f"failed: {str(e)}")

# dryrun_worker.py
from azure.storage.fileshare import ShareServiceClient
from datetime import datetime, timedelta
from config import AZURE_FILES_CONN_STRING
from dryrun_tracker import update_dryrun_progress
from audit_logger import is_excluded, is_date_dir

def dryrun_file_share(job_id, share_name):
    try:
        client = ShareServiceClient.from_connection_string(AZURE_FILES_CONN_STRING)
        share_client = client.get_share_client(share_name)
        now = datetime.utcnow()
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
                        update_dryrun_progress(job_id, candidate={"type": "Directory", "path": full_path})
                        continue
                    walk(share_client.get_directory_client(full_path), full_path)
                else:
                    file_client = share_client.get_file_client(full_path)
                    props = file_client.get_file_properties()
                    processed += 1
                    if props["last_modified"] < now - timedelta(days=30):
                        update_dryrun_progress(job_id, candidate={"type": "File", "path": full_path})

                if processed % 10 == 0:
                    update_dryrun_progress(job_id, progress=(processed % 100))

        walk(share_client.get_directory_client(""))
        update_dryrun_progress(job_id, status="completed", progress=100)
    except Exception as e:
        update_dryrun_progress(job_id, status=f"failed: {str(e)}")