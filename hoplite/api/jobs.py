from hoplite.utils import server_logging
from hoplite.serializer import hoplite_loads
from flask import Blueprint, request
from hoplite.api.helpers import job_manager, jsonify
from hoplite.exceptions import (
    JobDoesNotExistError,
    JobPluginDoesNotExistError,
    JobNotStartedError,
    JobAlreadyStartedError)

logger = server_logging.get_server_logger(__name__)


bp = Blueprint('jobs', __name__)


@bp.route("", methods=['GET'])
def get_jobs():
    logger.debug(
        "HTTP: Request All Jobs - From: {0}".format(request.remote_addr))
    jobs = job_manager.all_jobs()
    jobs_as_dict = []
    for job in jobs:
        jobs_as_dict.append(job.to_dict())
    return jsonify(jobs=jobs_as_dict)


@bp.route("", methods=['POST'])
def create_job():
    job_dict = hoplite_loads(request.data)
    name = job_dict.get('name', "default")
    config = job_dict.get('config', {})
    running = job_dict.get('running', False)
    port = job_dict.get('port', 5000)
    try:
        logger.debug(
            "HTTP: Request Create Job:{0} - From: {1}".format(
                name, request.remote_addr))
        job = job_manager.create_job(name, config, running, port)
    except JobPluginDoesNotExistError, e:
        return jsonify(error=str(e)), 400
    return jsonify(**job.to_dict())


@bp.route("/<job_uuid_string>", methods=['GET', 'PUT'])
def created_job(job_uuid_string):
    logger.debug(
        "HTTP: {0} Status Job UUID:{1} - From: {2}".format(
            request.method, job_uuid_string, request.remote_addr))
    try:
        job = job_manager.get_job(job_uuid_string)
    except (JobDoesNotExistError, ValueError) as e:
        return jsonify(error=str(e)), 404
    if request.method == 'PUT':
        r_json = hoplite_loads(request.data)
        if r_json.get("status", None):
            job.update_status(r_json["api_key"], r_json["status"])
    return jsonify(**job.to_dict())


@bp.route("/<job_uuid>/start", methods=['PUT'])
def start_job(job_uuid):
    try:
        logger.debug(
            "HTTP: Start Job UUID:{0} - From: {1}".format(
                job_uuid, request.remote_addr))
        job = job_manager.get_job(job_uuid)
        job.start()
    except JobDoesNotExistError, e:
        return jsonify(error=str(e)), 404
    except JobAlreadyStartedError, e:
        return jsonify(error=str(e)), 403
    return jsonify(uuid=job.uuid, started=True)


@bp.route("/<job_uuid>/kill", methods=['PUT'])
def kill_job(job_uuid):
    logger.debug(
        "HTTP: Terminate Job UUID:{0} - From: {1}".format(
            job_uuid, request.remote_addr))
    try:
        job = job_manager.get_job(job_uuid)
        job.kill()
    except JobDoesNotExistError, e:
        return jsonify(error=str(e)), 404
    except JobNotStartedError, e:
        return jsonify(error=str(e)), 403
    return jsonify(uuid=job.uuid, killed=True)


@bp.route("/running")
def running_jobs():
    logger.debug(
        "HTTP: Get Running Jobs- From: {0}".format(request.remote_addr))
    running_jobs = []
    jobs = job_manager.all_jobs()
    for job in jobs:
        if job.running():
            running_jobs.append(job.to_dict())
    return jsonify(jobs=running_jobs)
