import os
import re
from dotenv import load_dotenv
from azure.storage.fileshare import ShareServiceClient
from progress_tracker import update_progress
from datetime import datetime, timezone
from logger import get_logger  # ✅ Custom logger

# Load env and config
load_dotenv()
logger = get_logger("cleanup_worker")

RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", 30))
EXCLUDE_DIRS = [d.strip().lower() for d in os.getenv("EXCLUDE_DIRS", "").split(",") if d.strip()]

def should_exclude(path):
    """Check if path should be excluded based on EXCLUDE_DIRS or contains 'config'."""
    path_lower = path.lower()
    if "config" in path_lower:
        return True
    return any(path_lower.startswith(excl) for excl in EXCLUDE_DIRS)

def is_date_folder(name):
    """Check if folder name matches YYYY-MM-DD format."""
    return re.match(r"\d{4}-\d{2}-\d{2}$", name)

def cleanup_file_share(job_id, conn_str, share_name):
    try:
        logger.info(f"🧹 Starting cleanup for share: {share_name}")
        client = ShareServiceClient.from_connection_string(conn_str)
        share_client = client.get_share_client(share_name)

        total_processed = total_deleted = total_failed = 0

        def walk_and_clean(dir_path=""):
            nonlocal total_processed, total_deleted, total_failed

            items = list(share_client.list_directories_and_files(directory_name=dir_path))

            for item in items:
                item_path = f"{dir_path}/{item.name}" if dir_path else item.name

                if should_exclude(item_path):
                    logger.info(f"⏩ Skipping excluded path: {item_path}")
                    continue

                try:
                    if item.is_directory:
                        # Always recurse into subdirectory
                        logger.info(f"📂 Scanning directory: {item_path}")
                        walk_and_clean(item_path)

                        # If it's a date folder and old enough, attempt delete after cleaning
                        if is_date_folder(item.name):
                            dir_props = share_client.get_directory_client(item_path).get_directory_properties()
                            last_modified = dir_props['last_modified']
                            now = datetime.now(timezone.utc)
                            age_days = (now - last_modified).days

                            if age_days > RETENTION_DAYS:
                                try:
                                    share_client.delete_directory(item_path)
                                    logger.info(f"🗑 Deleted old date folder: {item_path} ({age_days} days old)")
                                    total_deleted += 1
                                except Exception as e:
                                    logger.warning(f"⚠️ Failed to delete folder {item_path} after cleanup: {e}")
                                    total_failed += 1

                    else:
                        file_client = share_client.get_file_client(item_path)
                        props = file_client.get_file_properties()
                        last_modified = props['last_modified']
                        now = datetime.now(timezone.utc)
                        age_days = (now - last_modified).days

                        total_processed += 1
                        if age_days > RETENTION_DAYS:
                            file_client.delete_file()
                            logger.info(f"🗑 Deleted old file: {item_path} ({age_days} days old)")
                            total_deleted += 1

                except Exception as e:
                    total_failed += 1
                    logger.warning(f"⚠️ Could not process {item_path}: {e}")

        walk_and_clean()

        update_progress(
            job_id=job_id,
            status="Completed",
            processed=total_processed,
            deleted=total_deleted,
            failed=total_failed,
            message="Cleanup finished successfully."
        )

    except Exception as e:
        logger.exception(f"❌ Error running cleanup for {share_name}")
        update_progress(job_id, status="Failed", message=str(e))
