```markdown
# Azure File Share Cleanup Monitor

This project is a scheduled cleanup utility designed for Kubernetes PVCs backed by Azure File Shares. It reads PVC metadata from Azure Table Storage, evaluates cleanup eligibility based on schedule intervals, and removes files or folders older than a configured retention period.

---

## 🚀 Features

- Cleans Azure File Share contents based on age.
- Skips excluded folders or folders containing "config" (case-insensitive).
- Deletes empty date-named folders (e.g., `2025-07-01`) if older than retention.
- Stores cleanup job status in Azure Table Storage.
- Periodically monitors PVCs and schedules cleanups.
- Logs activity to both console and rotating log file.
- Built-in progress tracking (`CleanupJobTracking` table).

---

## 📁 Project Structure

```

azure-fileshare-cleanup/
├── cleanup_worker.py         # Core cleanup logic
├── pvc_monitor.py            # Scheduler and monitoring loop
├── progress_tracker.py       # Tracks job progress in Azure Table
├── storage_table.py          # Table operations and storage connections
├── logger.py                 # Reusable logger configuration
├── .env                      # Configuration file
└── README.md                 # You're here

````

---

## ⚙️ Configuration (.env)

Create a `.env` file in the project root:

```env
# Azure Tables
AZURE_TABLE_CONN_STRING=DefaultEndpointsProtocol=...;AccountKey=...

# Cleanup logic
RETENTION_DAYS=30
EXCLUDE_DIRS=backups,temp,ignorethis
MONITOR_INTERVAL_HOURS=1

# Logging
LOG_LEVEL=INFO
LOG_FILE=cleanup.log
LOG_MAX_BYTES=5242880
LOG_BACKUP_COUNT=3
````

---

## 🧪 How It Works

1. **PVC Monitoring**

   * `pvc_monitor.py` reads PVCs from the `PVCMetadata` table.
   * Determines if cleanup should run by comparing `last_run + schedule_hours`.
   * If no existing job found, creates tracking entry.

2. **Cleanup Execution**

   * `cleanup_worker.py` walks the Azure File Share recursively.
   * Deletes:

     * Files older than `RETENTION_DAYS`.
     * Date-named folders (e.g. `2024-10-12`) older than retention period (after emptying).
   * Skips:

     * Paths listed in `EXCLUDE_DIRS`.
     * Any directory or file containing `config` (case-insensitive).

3. **Tracking**

   * Job metadata is written to `CleanupJobTracking` Azure Table.
   * Fields include `start_time`, `last_update`, `status`, `deleted`, `failed`, etc.

---

## 📝 Azure Table Schema

* **PVCMetadata**

  * `PartitionKey`: usually `pvc`
  * `RowKey`: unique PVC ID
  * `share_name`: Azure File Share name
  * `storage_account`: Name of the Azure Storage Account
  * `schedule_hours`: Interval (in hours) between cleanup runs

* **CleanupJobTracking**

  * `PartitionKey`: `cleanup`
  * `RowKey`: `share_name`
  * `status`: `Scheduled`, `Running`, `Completed`, `Failed`
  * `start_time`, `last_update`, `message`, `processed`, `deleted`, `failed`

---

## 🛠️ Running the Monitor

```bash
python pvc_monitor.py
```

Logs will appear in the terminal and the `cleanup.log` file (with rotation enabled).

---

## 🧼 Example Output

```
2025-07-19 04:00:00,123 [INFO] 📡 PVC Monitor started
2025-07-19 04:00:02,456 [INFO] 🔍 Found 2 PVCs to check
2025-07-19 04:00:04,789 [INFO] 🔐 Retrieved connection string for storage account: devops-aks
2025-07-19 04:00:05,001 [INFO] ⏱ Scheduling cleanup for share: pvc-123abc
2025-07-19 04:00:05,234 [INFO] 🧹 Starting cleanup for share: pvc-123abc
2025-07-19 04:00:07,890 [INFO] 🗑 Deleted old file: archive/report.txt (45 days old)
```

---

## ✅ Requirements

* Python 3.8+
* Azure Storage Tables and File Shares
* Tables: `PVCMetadata`, `CleanupJobTracking`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 📦 Future Enhancements

* Email or webhook notifications on failure
* Dashboard or CLI status viewer
* Integration with Kubernetes API for dynamic PVC discovery

---

## 👨‍💻 Maintainer

**Armughan Bhutta**
For support or suggestions, please raise an issue or contact directly.

---

## 📜 License

MIT License

```

Let me know if you'd like a `requirements.txt` or `.env.example` as well.
```
