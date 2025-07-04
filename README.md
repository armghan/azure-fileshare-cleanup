# Azure File Share Cleanup API

A Flask-based API to:
- Clean Azure File Share files older than 30 days
- Remove date-based folders (e.g., `2024-01-01`) older than 30 days
- Exclude config directories and specific folders
- Track progress using Job ID
- Write deletion logs to Azure Table Storage in a separate account
- Supports dry-run to simulate deletions

## 🔧 Setup

### 1. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Configure `.env`
```bash
cp .env.example .env
```

Fill in your Azure Storage connection strings and table name.

### 4. Run the API
```bash
python app.py
```

## 🧪 Cleanup API

### Start Cleanup
```http
POST /start-cleanup/fileshare
{
  "share_name": "your-fileshare-name"
}
```

### Check Progress
```http
GET /progress/<job_id>
```

## 🧪 Dry Run API

### Start Dry Run
```http
POST /dry-run/fileshare
{
  "share_name": "your-fileshare-name"
}
```

### Check Dry Run Progress
```http
GET /dry-run/progress/<job_id>
```

## 📬 Logs
- All actual deletions are logged to Azure Table Storage in a separate account
- Dry runs do not perform deletions, only simulate and return paths

## ✅ Exclusions
- Paths containing "config"
- Folders: Outbound, ConfigBackup, certificates
- Skips recent folders (under 30 days)