from hoplite.utils import server_logging
from flask import Blueprint, request
from hoplite.api.helpers import job_manager, jsonify

logger = server_logging.get_server_logger(__name__)

bp = Blueprint("job_plugins", __name__)


@bp.route("")
def available_job_plugins():
    logger.debug(
        "HTTP: Get Available Job Plugins- From: {0}".format(
            request.remote_addr))
    return jsonify(job_plugins=job_manager.available_job_plugins())
