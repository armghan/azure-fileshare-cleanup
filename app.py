from flask import Flask, request, jsonify
from threading import Thread
from progress_tracker import create_job, get_progress
from cleanup_worker import cleanup_file_share
from dryrun_tracker import create_dryrun_job, get_dryrun_progress
from dryrun_worker import dryrun_file_share
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set log level from environment or default to INFO
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

# Configure logging
logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)')
logger = logging.getLogger(__name__)

# Reduce Flask and Azure SDK log noise unless debugging
#logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('azure').setLevel(logging.WARNING)
#logging.getLogger('urllib3').setLevel(logging.WARNING)

app = Flask(__name__)

@app.route('/start-cleanup/fileshare', methods=['POST'])
def start_cleanup():
    try:
        share_name = request.json.get("share_name")
        if not share_name:
            return jsonify({"error": "Missing 'share_name'"}), 400

        job_id = create_job()
        Thread(target=cleanup_file_share, args=(job_id, share_name)).start()
        return jsonify({"job_id": job_id}), 202
    except Exception as e:
        logger.error("Failed to start cleanup job", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/progress/<job_id>', methods=['GET'])
def check_progress(job_id):
    return jsonify(get_progress(job_id))

@app.route('/dry-run/fileshare', methods=['POST'])
def start_dryrun():
    try:
        share_name = request.json.get("share_name")
        if not share_name:
            return jsonify({"error": "Missing 'share_name'"}), 400

        job_id = create_dryrun_job()
        Thread(target=dryrun_file_share, args=(job_id, share_name)).start()
        return jsonify({"job_id": job_id, "message": "Dry run started"}), 202
    except Exception as e:
        logger.error("Failed to start dry-run job", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/dry-run/progress/<job_id>', methods=['GET'])
def check_dryrun_progress(job_id):
    return jsonify(get_dryrun_progress(job_id))

if __name__ == '__main__':
    debug_mode = log_level_str == "DEBUG"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
