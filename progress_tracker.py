from threading import Lock
from uuid import uuid4

progress_data = {}
lock = Lock()

def create_job():
    job_id = str(uuid4())
    with lock:
        progress_data[job_id] = {"status": "pending", "progress": 0, "deleted": 0}
    return job_id

def update_progress(job_id, status=None, progress=None, deleted=None):
    with lock:
        if job_id in progress_data:
            if status:
                progress_data[job_id]["status"] = status
            if progress is not None:
                progress_data[job_id]["progress"] = progress
            if deleted is not None:
                progress_data[job_id]["deleted"] = deleted

def get_progress(job_id):
    with lock:
        return progress_data.get(job_id, {"error": "Invalid job ID"})