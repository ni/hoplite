import logging
import os
import random
import tempfile
import time

from exceptions import ExternalCustomError, ExternalEmptyError
from hoplite.remote_enabler import remotify

logger = logging.getLogger(__name__)


@remotify(__name__)
class TestClass:
    class MyPrivateError(Exception):
        pass

    def __init__(self, string_value=None, number_value=None):
        self.string_value = string_value
        self.number_value = number_value
        self.file_contents = "".join([random.choice('abcdefghijklmnopqrstuvwxyz') for _ in xrange(8)])

    def return_none(self):
        """
        Used to test that a None value can be returned properly
        :return: None
        """
        None

    def return_number(self):
        """
        Used to test that a single value can be returned properly
        :return: A number, 777
        """
        return 777

    def return_tuple(self):
        """
        Used to test that a tuple can be returned properly
        :return: A tuple containing a string, an int, and a float
        """
        return 'All', 4, 1.11

    def return_single_list(self):
        """
        Used to test that a single list can be returned properly
        :return: A list containing several strings
        """
        return ['This', 'is', 'a', 'list']

    def do_math(self, number_1, number_2):
        """
        Used to test that numeric arguments can be passed through as arguments
        :param number_1: Arbitrary number
        :param number_2: Arbitrary number
        :return: The product of the two arguments
        """
        return number_1 * number_2

    def pass_common_class(self, date):
        """
        Used to test that more complex class objects can be passed through as arguments
        :param date: Datetime object
        :return: A tuple containing the information stored in the datetime argument
        """
        return date.year, date.month, date.day, date.hour, date.minute, date.second, date.microsecond

    def pass_custom_class(self, dummy):
        """
        Used to test that custom class objects can be passed through as arguments
        :param dummy: DummyClass
        :return: The sum of numbers contained in the class
        """
        return dummy.add_numbers()

    def return_multiple_lists(self):
        """
        Used to test that a jagged, 2-dimensional list can be returned properly
        :return: A list of lists, each of which are different lengths and contain different values
        """
        return ['This', 'is', 1, 'list'], ['and', 'this', 'is', 'another', 'list']

    def get_class_variables(self):
        """
        Used to test that class member variables are transmitted to the remote
        function and then can be manipulated and returned properly
        :return: A string, and a number multiplied by two, both class variables
        """
        return self.string_value, self.number_value * 2

    def raise_type_error(self):
        """
        Test that normal exceptions can be raised properly
        :raise TypeError: Unconditionally raises Type Error
        """
        raise TypeError('___Failure1')

    def raise_custom_error(self):
        """
        Used to test that custom exceptions can be raised properly
        :raise ExternalEmptyError: Unconditionally raises Weird Error
        """
        raise ExternalEmptyError('___Failure2')

    def create_file(self):
        """
        Used to test remote file creation using a string stored in class instance
        :return: The name of the random temp file that was created
        """
        handle, filename = tempfile.mkstemp()
        with os.fdopen(handle, 'w') as fout:
            fout.write(self.file_contents)
        return filename

    def create_specified_file(self, filename, contents='default_contents'):
        """
        Used to test remote file creation using a string passed into the function. The filename
        is also passed in. This is specifically used to test the asynchronous functionality
        of the metaclass.
        """
        time.sleep(1)
        with open(filename, 'w') as fout:
            fout.write(contents)

    def call_nested_function(self):
        """
        Used to test that exception handling works properly when jobs are nested. This function
        starts a job that raises a type error.
        :raise TypeError: Raised when the function remote_raise_type_error is called
        """
        self.remote_raise_type_error('localhost:5001')

    def raise_private_error(self):
        """
        Used to test that private errors defined within a class cannot be properly pickled. This means
        that the exception should come out on the client side as a JobFailedError instead.
        :raise MyPrivateException: A private exception class
        """
        raise TestClass.MyPrivateError('___Failure3')

    def raise_public_error(self):
        """
        Used to test that externally defined, custom errors can be raised on the client side.
        :raise ExternalCustomError: Unconditionally raises ExternalCustomError
        """
        raise ExternalCustomError('___Failure4')

    def return_custom_exception(self):
        """
        Used to test that custom class instances (such as exceptions) can be returned
        :return: Returns an ExternalCustomError exception object
        """
        return ExternalCustomError('___Failure4')

    def long_job(self):
        """
        Used to test job timeouts on remotely called functions
        """
        time.sleep(7)

    def log_normal(self, dummy_var_1, dummy_var_2=None):
        logger.info('Logging in log_normal function')
        return str(dummy_var_1) + ' + ' + str(dummy_var_2)

    def log_nested_caller(self):
        logger.info('Currently in class caller function')
        self.log_nested_callee()

    def log_nested_callee(self):
        logger.info('Currently in class callee function')

    @staticmethod
    def static_return_number():
        """
        Used to test that static methods can be called remotely
        :return: A number, 999
        """
        return 999


class ParentClass(object):
    """
    Normal new-style class which doesn't do much at all.
    """
    def __init__(self, parent_value):
        self.parent_value = parent_value

    def func_1(self, value_to_add):
        return 1 + value_to_add + self.parent_value

    def func_2(self, value_to_add):
        return 2 + value_to_add + self.parent_value


@remotify(__name__)
class ChildClass(ParentClass):
    """
    Class which inherits from the ParentClass class. This is to make sure
    that it is possible to have a parent which doesn't use the metaclass, provided
    it inherits from object. In addition, this class exercises various features which
    are used by the metaclass, such as function arguments and return values. Also, values
    from ParentClass are used in calculating the function return values, in order to test
    that inherited classes don't get broken by the remotable system.
    """
    def __init__(self, child_value, parent_value):
        self.child_value = child_value
        ParentClass.__init__(self, parent_value)

    def func_3(self, value_to_add):
        return 3 + value_to_add + self.child_value + self.parent_value

    def func_4(self, value_to_add):
        return 4 + value_to_add + self.child_value + self.parent_value


class GrandchildClass(ChildClass):
    """
    Class which inherits from the ChildClass class. This is to make sure that the metaclass
    applied to ChildClass also gets applied to this class, GrandchildClass. Also, values
    from ChildClass and ParentClass are used in calculating the function return values, in
    order to test that inherited classes don't get broken by the remotable system.
    """
    def __init__(self, grandchild_value, child_value, parent_value):
        self.grandchild_value = grandchild_value
        ChildClass.__init__(self, child_value, parent_value)

    def func_5(self, value_to_add):
        return 5 + value_to_add + self.grandchild_value + self.child_value + self.parent_value

    def func_6(self, value_to_add):
        return 6 + value_to_add + self.grandchild_value + self.child_value + self.parent_value