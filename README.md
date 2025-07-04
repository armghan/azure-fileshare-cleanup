# Azure Fileshare Cleanup API

This project provides a Flask-based REST API to **list or delete old files and directories** in an Azure File Share that are older than a configurable retention period. It supports both **dry-run** (preview) and actual deletion, with **logging and progress tracking**.

---

## 🔧 Features

* Cleanup files/directories older than `RETENTION_DAYS` (default: 30)
* Dry-run mode to preview what would be deleted
* Separate log files for:

  * Deleted items (`logs/deleted.log`)
  * Dry-run candidates (`logs/dryrun.log`)
* Asynchronous background processing
* Simple job tracking via `/progress` endpoints
* Configurable log level and retention using `.env`

---

## 📁 Directory Structure

```
python-cleanup-api/
│
├── app.py
├── cleanup_worker.py
├── dryrun_worker.py
├── audit_logger.py
├── config.py
├── dryrun_tracker.py
├── progress_tracker.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
└── logs/
    ├── deleted.log
    └── dryrun.log
```

---

## 📦 Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## ⚙️ .env Configuration

Create a `.env` file in the root directory:

```
AZURE_FILES_CONN_STRING=your-fileshare-connection-string
LOG_LEVEL=INFO
RETENTION_DAYS=30
```

* `AZURE_FILES_CONN_STRING`: Connection string to your Azure File Share storage account.
* `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`
* `RETENTION_DAYS`: Number of days to retain files/directories. Older data will be deleted.

---

## 🚀 Running the API

```bash
python app.py
```

Default port is `5000`.

---

## 📡 API Endpoints

### 1. Start Cleanup

```bash
curl -X POST http://localhost:5000/start-cleanup/fileshare \
  -H "Content-Type: application/json" \
  -d '{"share_name": "your-fileshare-name"}'
```

**Response**:

```json
{ "job_id": "xxx-yyy-zzz" }
```

---

### 2. Start Dry Run

```bash
curl -X POST http://localhost:5000/dry-run/fileshare \
  -H "Content-Type: application/json" \
  -d '{"share_name": "your-fileshare-name"}'
```

**Response**:

```json
{ "job_id": "xxx-yyy-zzz", "message": "Dry run started" }
```

---

### 3. Check Cleanup Progress

```bash
curl http://localhost:5000/progress/<job_id>
```

**Response**:

```json
{ "progress": 80, "deleted": 120, "status": "pending" }
```

---

### 4. Check Dry Run Progress

```bash
curl http://localhost:5000/dry-run/progress/<job_id>
```

**Response**:

```json
{ "progress": 90, "total_candidates": 145, "status": "pending" }
```

---

## 📜 Logs

* `logs/deleted.log`: Contains entries of actually deleted items.
* `logs/dryrun.log`: Contains dry-run candidate items (what would be deleted).
* Console logs are controlled using `.env` variable `LOG_LEVEL`.

---

## ✅ Example Use Case

* Identify and clean up Azure File Share structures that are older than N days.
* Use dry-run to simulate and verify deletions.
* Track all deletions and dry-run evaluations via log files.

---

## 🧪 Tested With

* Python 3.8+
* `azure-storage-file-share`
* Flask 3.x

---

## 🛠 Notes

* No data is deleted in dry-run mode.
* App runs non-blocking jobs in background using Python threads.
* Does **not** use Azure Table Storage. All logs are local file-based.

---