import os
from datetime import datetime, timedelta, timezone
from config import RETENTION_DAYS
import logging

EXCLUDED_DIRS = {"Outbound", "ConfigBackup", "certificates"}

# Create logs directory if it doesn't exist
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Deleted item logger
deleted_logger = logging.getLogger("deleted_logger")
deleted_logger.setLevel(logging.INFO)
deleted_handler = logging.FileHandler(os.path.join(log_dir, "deleted.log"))
deleted_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
deleted_logger.addHandler(deleted_handler)

# Dry run item logger
dryrun_logger = logging.getLogger("dryrun_logger")
dryrun_logger.setLevel(logging.INFO)
dryrun_handler = logging.FileHandler(os.path.join(log_dir, "dryrun.log"))
dryrun_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
dryrun_logger.addHandler(dryrun_handler)

def ensure_table_exists():
    deleted_logger.info("✅ Local deleted log initialized at logs/deleted.log")
    dryrun_logger.info("✅ Local dry-run log initialized at logs/dryrun.log")

def log_deletion(share_name, item_path, item_type):
    try:
        deleted_at = datetime.now(timezone.utc).isoformat()
        deleted_logger.info(f"Deleted {item_type}: {item_path} from share '{share_name}' at {deleted_at}")
    except Exception as e:
        deleted_logger.error(f"❌ Failed to log deletion for {item_path}", exc_info=True)

def log_dryrun_candidate(share_name, item_path, item_type):
    try:
        evaluated_at = datetime.now(timezone.utc).isoformat()
        dryrun_logger.info(f"[DRYRUN] {item_type} would be deleted: {item_path} from share '{share_name}' at {evaluated_at}")
    except Exception as e:
        dryrun_logger.error(f"❌ Failed to log dry-run candidate for {item_path}", exc_info=True)

def is_excluded(path):
    return any(
        "config" in part.lower() or part in EXCLUDED_DIRS
        for part in path.strip("/").split("/")
    )

def is_date_dir(name):
    try:
        parsed_date = datetime.strptime(name, "%Y-%m-%d")
        return parsed_date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    except ValueError:
        return False
