import logging
import pickle
import sys
import traceback

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class HopliteError(Exception):
    """
    Base exception for all Hoplite errors
    """
    pass


# TODO: Write unit tests for the logic in this class
class JobFailedError(HopliteError):
    """
    Raised when there is an "exception" key in a job's status on the client.

    This exception can contain nested information regarding other exceptions
    which preceded it. Specifically, in cases where jobs call other jobs which
    raise exceptions, stack trace and other important information for every
    intermediate job can be preserved in a single exception.  This is useful
    for debugging in complex situations which require chaining of multiple
    jobs.
    """
    def __init__(self, address, uuid, traceback_object, previous_exception):
        """
        :param String address: Address of the host that was running the job
        :param String uuid: uuid of the job that threw the exception
        :param [(String, String, String, String)] traceback_object: Traceback
            object for the exception which occurred
        :param previous_exception: The information from the previously-raised
            exceptions
        """
        self.addr = address
        self.uuid = uuid
        self.traceback_object = traceback_object
        self.previous_exception = previous_exception

    @property
    def message(self):
        """
        Ensure that full info about the exception will always be retrieved when
        viewing the message
        :return:
        """
        return self.__str__()

    def __str__(self):
        """
        Provides useful information when printing information about this
        exception. This will display the full traces for each job which was
        called leading up to the root exception.

        :return: A string containing a full representation of all information
            contained in this exception. This includes stack traces for all
            jobs called before the exception occurred.
        """
        def single_traceback(traceback_object):
            trace_str = ''
            for line in traceback.extract_tb(traceback_object):
                trace_str += '      File "{0}", line {1}, in {2}'.format(line[0], line[1], line[2]) + '\n'
                trace_str += '         {0}'.format(line[3]) + '\n'
            return trace_str

        output = ''
        output += 'Full traceback for all jobs descended from current job:\n'
        output += '   In job with UUID: {}'.format(self.uuid) + '\n'
        output += '   Running on machine: {}'.format(self.addr) + '\n'
        output += '      Traceback:\n'
        output += single_traceback(self.traceback_object)

        previous_exception = self.previous_exception
        while (previous_exception is not None) and (previous_exception.get('type', None) is None):
            output += 'In job with UUID: {}'.format(previous_exception.get('uuid')) + '\n'
            output += 'Running on machine: {}'.format(previous_exception.get('address')) + '\n'
            output += '   Traceback:\n'
            output += single_traceback(pickle.loads(previous_exception.get('traceback')))
            previous_exception = previous_exception.get('previous_exception', None)

        output += '   Root Error Type: {}'.format(previous_exception.get('type')) + '\n'
        output += '   Root Error Message: {}'.format(previous_exception.get('message'))
        return output

    def raise_remote_exception(self):
        """
        Handles JobFailedErrors by trying to raise the same exception which was
        raised on the remote machine. This is useful in allowing a client to
        operate on a remote machine more transparently (i.e. it seems more like
        the operations are occurring on the local machine, since the exceptions
        raised on the remote machine are also raised on the local machine).
        This functionality is probably vulnerable to many corner cases, and
        might not be particularly reliable.

        Examines the JobFailedError exception information to determine what
        exception was originally raised on the remote machine. If that
        exception exists in scope on this machine (i.e. a currently-loaded
        module defines that exception), then that exception will be raised on
        the local machine. Otherwise, a JobFailedError exception will be
        raised.

        This is called as part of the RemotableMetaClass and Remotify
        decorator, and should not be manually called in most circumstances

        :raises JobFailedError: When the original exception cannot be raised
            for any reason, then the JobFailedError from which this was called
            is reraised.
        :raises Various Other Errors: When a known exception occurred in the
            remote job, then that exception will be raised
        """

        # Get to bottom-most exception (the original exception that was thrown)
        previous_exception = self.previous_exception
        while (previous_exception is not None) and ('type' not in previous_exception):
            previous_exception = previous_exception.get('previous_exception', None)

        exception_object_string = previous_exception.get('exception_object', None)

        exception_to_raise = self

        try:
            if exception_object_string:
                exception_object = pickle.loads(exception_object_string)
                if exception_object is not None:
                    exception_to_raise = exception_object
        except Exception as e:  # If unable to raise original exception, then reraise self
            pass
        finally:
            logger.info('Exception raised from remote machine "{}". Local traceback:\n{}\n'
                        'Remote exception info:\n{}'.format(self.addr,
                                                            traceback.print_tb(sys.exc_info()[2]),
                                                            traceback.format_exception(
                                                                type(exception_to_raise),
                                                                exception_to_raise,
                                                                self.traceback_object
                                                            )))
            raise type(exception_to_raise), exception_to_raise, self.traceback_object.tb_next.tb_next
            

class JobPluginLoadError(HopliteError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class JobNotStartedError(HopliteError):
    def __init__(self, uuid):
        self.msg = "Job UUID: {0} has not been started".format(uuid)

    def __str__(self):
        return self.msg


class JobAlreadyStartedError(HopliteError):
    def __init__(self, uuid):
        self.msg = "Job UUID: {0} you cannot start a job more than once".format(uuid)

    def __str__(self):
        return self.msg


class NotAuthorizedError(HopliteError):
    def __init__(self):
        pass

    def __str__(self):
        return "You are not authorized to perform this action"


class JobDoesNotExistError(HopliteError):
    def __init__(self, message="Job does not exist"):
        self.message = message

    def __str__(self):
        return self.message


class JobPluginDoesNotExistError(HopliteError):
    def __init__(self, name):
        self.job_plugin_name = name

    def __str__(self):
        return "Job plugin '{0}' does not exist".format(self.job_plugin_name)


class InternalServerError(HopliteError):
    def __init__(self, message="Something went wrong on the server"):
        self.message = message

    def __str__(self):
        return self.message


class TimeoutError(HopliteError):
    def __init__(self, uuid=0):
        self._uuid = uuid

    def __str__(self):
        return "Waiting for job {0} timed out".format(self._uuid)


class ConnectionError(HopliteError):
    def __init__(self, addr):
        self.addr = addr

    def __str__(self):
        return 'Hoplite could not be contacted on host "{0}". Check that IP ' \
               'address/hostname and port are correct, and (if using ' \
               'hostname) check that DNS server is correctly configured. ' \
               'Also check that Hoplite server is running on the ' \
               'host.'.format(self.addr)
