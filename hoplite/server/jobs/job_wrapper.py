import pickle
import sys
from tblib import pickling_support
import traceback

from hoplite.utils import server_logging
from hoplite.plugin_manager import EntryPointManager
from hoplite.exceptions import JobFailedError

# This makes it so that traceback objects can be pickled
pickling_support.install()


def job_wrapper(pipe_to_parent, entry_point_name, config, status_updater,
                entry_point_group_name='hoplite.jobs', uuid=''):
    """
    A picklable function that is used to start the job. It loads the specified
    module and calls run on it with the correct parameters.

    In the event of an error occurring in the job, the error is bubbled up to
    the highest parent of the job. This is done by encapsulating each exception
    into a JobFailedError, which is raised to cause the bubbling action. Since
    Exceptions aren't picklable, information from previous exceptions is put
    into a dictionary.

    This exception bubbling is useful for situations in which jobs are used to
    call other jobs. The stack trace for each "level" is saved, and the entire
    list of jobs with their respective traces can be displayed at the top level
    (where the JobFailedError is handled).
    """
    module = EntryPointManager(
        entry_point_group_name).get_plugin_module_by_name(entry_point_name)
    logger = server_logging.get_job_logger(module.__name__, uuid)
    try:
        module.run(config, status_updater)
    except JobFailedError as e:
        logger.error(
            "A job raised an exception and it was not caught."
            " Address: {0} UUID: {1}".format(e.addr, e.uuid))
        logger.error(
            "Exception Traceback: {0}".format(
                traceback.format_tb(e.traceback_object)))
        _, _, tb = sys.exc_info()
        traceback_object = tb
        exception_dictionary = {
            "address": e.addr,
            "uuid": e.uuid,
            "traceback": e.traceback_object,
            "previous_exception": e.previous_exception
        }
        pass_to_parent = {
            "traceback": traceback_object,
            "previous_exception": exception_dictionary
        }
        pipe_to_parent.send(pass_to_parent)
    except Exception as e:
        except_type, except_class, tb = sys.exc_info()
        traceback_object = tb
        type_string = str(except_type)
        try:
            pickled_exception = pickle.dumps(e)
        except pickle.PicklingError:
            pickled_exception = None

        exception_dictionary = {
            "type": type_string,
            "message": e.message,
            "exception_object": pickled_exception
        }
        pass_to_parent = {
            "traceback": pickle.dumps(traceback_object),
            "previous_exception": exception_dictionary
        }
        logger.error("Job UUID:{0} Type:{1} Finished with except type:{2} "
                     "except class:{3} traceback:{4}".format(
                        uuid, entry_point_name,
                        except_type, except_class, traceback.format_tb(tb)))
        pipe_to_parent.send(pass_to_parent)
    logger.debug("Finished running UUID:{0}".format(uuid))
