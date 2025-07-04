from flask import Flask, request, jsonify
from threading import Thread
from progress_tracker import create_job, get_progress
from cleanup_worker import cleanup_file_share
from dryrun_tracker import create_dryrun_job, get_dryrun_progress
from dryrun_worker import dryrun_file_share

app = Flask(__name__)

@app.route('/start-cleanup/fileshare', methods=['POST'])
def start_cleanup():
    share_name = request.json.get("share_name")
    if not share_name:
        return jsonify({"error": "Missing 'share_name'"}), 400

    job_id = create_job()
    Thread(target=cleanup_file_share, args=(job_id, share_name)).start()
    return jsonify({"job_id": job_id}), 202

@app.route('/progress/<job_id>', methods=['GET'])
def check_progress(job_id):
    return jsonify(get_progress(job_id))

@app.route('/dry-run/fileshare', methods=['POST'])
def start_dryrun():
    share_name = request.json.get("share_name")
    if not share_name:
        return jsonify({"error": "Missing 'share_name'"}), 400

    job_id = create_dryrun_job()
    Thread(target=dryrun_file_share, args=(job_id, share_name)).start()
    return jsonify({"job_id": job_id, "message": "Dry run started"}), 202

@app.route('/dry-run/progress/<job_id>', methods=['GET'])
def check_dryrun_progress(job_id):
    return jsonify(get_dryrun_progress(job_id))

if __name__ == '__main__':
    app.run(debug=True)