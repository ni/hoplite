import logging
import time

from exceptions import ExternalCustomError, ExternalEmptyError
from hoplite.remote_enabler import remotify

logger = logging.getLogger(__name__)


@remotify(__name__)
def return_none():
    """
    Used to test that a None value can be returned properly
    :return: None
    """
    None


@remotify(__name__)
def return_number():
    """
    Used to test that a single value can be returned properly
    :return: A number, 777
    """
    return 777


@remotify(__name__)
def return_tuple():
    """
    Used to test that a tuple can be returned properly
    :return: A tuple containing a string, an int, and a float
    """
    return 'All', 4, 1.11


@remotify(__name__)
def return_single_list():
    """
    Used to test that a single list can be returned properly
    :return: A list containing several strings
    """
    return ['This', 'is', 'a', 'list']


@remotify(__name__)
def return_multiple_lists():
    """
    Used to test that a jagged, 2-dimensional list can be returned properly
    :return: A list of lists, each of which are different lengths and contain
        different values
    """
    return ['This', 'is', 1, 'list'], ['and', 'this', 'is', 'another', 'list']


@remotify(__name__)
def do_math(number_1, number_2):
    """
    Used to test that numeric arguments can be passed through as arguments
    :return:
    """
    return number_1 * number_2


@remotify(__name__)
def pass_common_class(date):
        """
        Used to test that more complex class objects can be passed through as
        arguments
        :param date: Datetime object
        :return: A tuple containing the information stored in the datetime
        argument
        """
        return date.year, date.month, date.day, date.hour, date.minute, date.second, date.microsecond


@remotify(__name__)
def pass_custom_class(dummy):
        """
        Used to test that custom class objects can be passed through as'
        arguments
        :param dummy: DummyClass
        :return: The sum of numbers contained in the class
        """
        return dummy.add_numbers()


@remotify(__name__)
def raise_type_error():
    """
    Test that normal exceptions can be raised properly
    :raise TypeError: Unconditionally raises Type Error
    """
    raise TypeError('___Failure1')


@remotify(__name__)
def raise_custom_error():
    """
    Used to test that custom exceptions can be raised properly
    :raise ExternalEmptyError: Unconditionally raises ExternalEmptyError
    """
    raise ExternalEmptyError('___Failure2')


@remotify(__name__)
def create_specified_file(filename, contents='default_contents'):
    """
    Used to test remote file creation using a string passed into the function.
    The filename is also passed in. This is specifically used to test the
    asynchronous functionality of the metaclass.
    """
    time.sleep(1)
    with open(filename, 'w') as fout:
        fout.write(contents)


@remotify(__name__)
def call_nested_function():
    """
    Used to test that exception handling works properly when jobs are nested.
    This function starts a job that raises a type error.
    :raise TypeError: Raised when the function remote_raise_type_error is
        called
    """
    remote_raise_type_error('localhost:5001')


@remotify(__name__)
def raise_private_error():
    """
    Used to test that private errors defined within a class cannot be properly
    pickled. This means that the exception should come out on the client side
    as a JobFailedError instead.
    :raise JobFailedError: Attempts to raise MyPrivateError, but will fail and
        instead raise JobFailedError
    """
    class MyPrivateError(Exception):
        pass
    raise MyPrivateError('___Failure3')


@remotify(__name__)
def raise_public_error():
    """
    Used to test that externally defined, custom errors can be raised on the
    client side.
    :raise ExternalCustomError: Unconditionally raises ExternalCustomError
    """
    raise ExternalCustomError('___Failure4')


@remotify(__name__)
def return_custom_exception():
    """
    Used to test that custom class instances (such as exceptions) can be
    returned
    :return: Returns an ExternalCustomError exception object
    """
    return ExternalCustomError('___Failure4')


@remotify(__name__)
def long_job():
    """
    Used to test job timeouts on remotely called functions
    """
    time.sleep(7)


@remotify(__name__)
def log_normal(dummy_var_1, dummy_var_2=None):
    logger.info('Logging in log_normal function')
    return str(dummy_var_1) + ' + ' + str(dummy_var_2)


@remotify(__name__)
def log_nested_caller():
    logger.info('Currently in caller function')
    log_nested_callee()


def log_nested_callee():
    logger.info('Currently in callee function')
