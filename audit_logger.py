import logging
from datetime import datetime, timedelta, timezone
import os

EXCLUDED_DIRS = {"Outbound", "ConfigBackup", "certificates"}
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", 30))

# Ensure base log directories exist
os.makedirs("logs/deleted", exist_ok=True)
os.makedirs("logs/dryrun", exist_ok=True)

# Cache for loggers per share name
_deleted_loggers = {}
_dryrun_loggers = {}

def get_logger(logger_dict, base_dir, share_name, prefix):
    if share_name not in logger_dict:
        logger = logging.getLogger(f"{prefix}_{share_name}")
        logger.setLevel(logging.INFO)
        log_path = os.path.join("logs", base_dir, f"{share_name}.log")
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger_dict[share_name] = logger
    return logger_dict[share_name]

def log_deletion(share_name, item_path, item_type):
    try:
        deleted_at = datetime.now(timezone.utc).isoformat()
        logger = get_logger(_deleted_loggers, "deleted", share_name, "deleted")
        logger.info(f"Deleted {item_type}: {item_path} at {deleted_at}")
    except Exception as e:
        logger = get_logger(_deleted_loggers, "deleted", share_name, "deleted")
        logger.error(f"❌ Failed to log deletion for {item_path}", exc_info=True)

def log_dryrun_candidate(share_name, item_path, item_type):
    try:
        evaluated_at = datetime.now(timezone.utc).isoformat()
        logger = get_logger(_dryrun_loggers, "dryrun", share_name, "dryrun")
        logger.info(f"[DRYRUN] {item_type} would be deleted: {item_path} at {evaluated_at}")
    except Exception as e:
        logger = get_logger(_dryrun_loggers, "dryrun", share_name, "dryrun")
        logger.error(f"❌ Failed to log dry-run candidate for {item_path}", exc_info=True)

def is_excluded(path):
    return any(
        "config" in part.lower() or part in EXCLUDED_DIRS
        for part in path.strip("/").split("/")
    )

def is_date_dir(name, now=None):
    try:
        parsed_date = datetime.strptime(name, "%Y-%m-%d")
        now = now or datetime.now(timezone.utc)
        return parsed_date.replace(tzinfo=timezone.utc) < now - timedelta(days=RETENTION_DAYS)
    except ValueError:
        return False
