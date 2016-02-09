import werkzeug
from werkzeug.local import LocalProxy
from hoplite.serializer import hoplite_dumps


# Jsonify that uses hoplite's serial decoder
def jsonify(*args, **kwargs):
    """
        jsonify that uses hoplite's serial encoder
    """
    return werkzeug.Response(
        hoplite_dumps(dict(*args, **kwargs)), mimetype='application/json')


# This gets set by the app factory when the app is created
manager = None


def get_job_manager():
    return manager

job_manager = LocalProxy(get_job_manager)
