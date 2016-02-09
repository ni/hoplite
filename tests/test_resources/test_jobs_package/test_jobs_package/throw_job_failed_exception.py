import sys

from hoplite.exceptions import JobFailedError


def run(config, status):
    address = "10.2.1.1"
    uuid = "5"
    # Get an arbitrary traceback to use for testing
    try:
        raise TypeError()
    except:
        test_traceback = sys.exc_info()[2]
    previous_exception = {
        "type": "Test Type String",
        "message": "Test Message",
        "exception_object": 'pickled_string'
    }

    raise JobFailedError(address, uuid, test_traceback, previous_exception)
