from threading import Lock
from uuid import uuid4

dryrun_data = {}
lock = Lock()

def create_dryrun_job():
    job_id = str(uuid4())
    with lock:
        dryrun_data[job_id] = {"status": "pending", "progress": 0, "scanned": 0}
    return job_id

def update_dryrun_progress(job_id, status=None, progress=None, scanned=None):
    with lock:
        if job_id in dryrun_data:
            if status:
                dryrun_data[job_id]["status"] = status
            if progress is not None:
                dryrun_data[job_id]["progress"] = progress
            if scanned is not None:
                dryrun_data[job_id]["scanned"] = scanned

def get_dryrun_progress(job_id):
    with lock:
        if job_id in dryrun_data:
            return {
                "progress": dryrun_data[job_id]["progress"],
                "status": dryrun_data[job_id]["status"],
                "scanned": dryrun_data[job_id].get("scanned", 0)
            }
        return {"error": "Invalid dry-run job ID"}