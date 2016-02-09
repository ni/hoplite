import datetime
import logging
import logging.handlers
import os
import psutil
import random
import re
import string
import sys
import tempfile
import time
import unittest2

from hoplite.client.remote_job_manager import RemoteJobManager
from hoplite.exceptions import JobFailedError, TimeoutError
from hoplite.public_api import wait_for_hoplite

sys.path.append(os.path.realpath(__file__))
import remotable_test_resources.remotable_class as remotable_class
from remotable_test_resources.dummy_class import DummyClass
import remotable_test_resources.remotable_module as remotable_module


def start_hoplite_server(port_num):
    proc = psutil.Popen(
        '{} -c "import hoplite.main; hoplite.main.server_main([\'--port={}\'])"'.format(sys.executable, port_num)
    )
    wait_for_hoplite('localhost', port_num)
    return proc


def tear_down_hoplite(process):
    l = process.get_children()
    for child in l:
        child.terminate()
        child.wait()
    process.terminate()
    process.wait()
    time.sleep(.5)


class TestMetaClassInjection(unittest2.TestCase):
    def setUp(self):
        self.class_instance = remotable_class.TestClass()

    def tearDown(self):
        pass

    def test_meta_class_injects_functions(self):
        class_attribs = dir(self.class_instance)

        function_names = [
            'return_none',
            'return_number',
            'return_tuple',
            'return_single_list',
            'return_multiple_lists',
            'do_math',
            'pass_common_class',
            'pass_custom_class',
            'get_class_variables',
            'raise_type_error',
            'raise_custom_error',
            'create_file',
            'create_specified_file',
            'call_nested_function',
            'raise_private_error',
            'raise_public_error',
            'return_custom_exception',
            'long_job',
            'log_normal'
        ]

        for name in function_names:
            self.assertIn('remote_' + name, class_attribs)
            self.assertIn('remote_async_' + name, class_attribs)


class TestModuleInjection(unittest2.TestCase):
    def test_remotable_functions_injected_in_module(self):
        class_attribs = dir(remotable_module)

        function_names = [
            'return_none',
            'return_number',
            'return_tuple',
            'return_single_list',
            'return_multiple_lists',
            'do_math',
            'pass_common_class',
            'pass_custom_class',
            'raise_type_error',
            'raise_custom_error',
            'create_specified_file',
            'call_nested_function',
            'raise_private_error',
            'raise_public_error',
            'return_custom_exception',
            'long_job',
            'log_normal'
        ]

        for name in function_names:
            self.assertIn('remote_' + name, class_attribs)
            self.assertIn('remote_async_' + name, class_attribs)


class TestRemotableClassCapabilities(unittest2.TestCase):
    def setUp(self):
        """
        This function has to use subprocess instead of multiprocessing. Otherwise, tests fail
        with the error "daemonic processes are not allowed to have children". This way, hoplite is
        run in a separate process.
        :return:
        """
        self.proc = start_hoplite_server(5001)
        self.class_instance = remotable_class.TestClass('this_is@a#string', 12349)

    def tearDown(self):
        tear_down_hoplite(self.proc)
        time.sleep(.5)

    def test_return_none(self):
        ret = self.class_instance.remote_return_none('localhost:5001')
        self.assertIsNone(ret)

    def test_return_number(self):
        ret = self.class_instance.remote_return_number('localhost:5001')
        self.assertEqual(ret, 777)

    def test_return_tuple(self):
        ret = self.class_instance.remote_return_tuple('localhost:5001')
        self.assertTrue(type(ret) == tuple)
        self.assertTupleEqual(ret, ('All', 4, 1.11))

    def test_return_list(self):
        ret = self.class_instance.remote_return_single_list('localhost:5001')
        self.assertTrue(type(ret) == list)
        self.assertListEqual(ret, ['This', 'is', 'a', 'list'])

    def test_return_multiple_lists(self):
        ret = self.class_instance.remote_return_multiple_lists('localhost:5001')
        self.assertTrue(type(ret) == tuple)
        self.assertListEqual(ret[0], ['This', 'is', 1, 'list'])
        self.assertListEqual(ret[1], ['and', 'this', 'is', 'another', 'list'])

    def test_do_math(self):
        ret = self.class_instance.remote_do_math('localhost:5001', 17, 13.5)
        self.assertEqual(ret, 17 * 13.5)

    def test_pass_common_class(self):
        date = datetime.datetime.now()
        ret = self.class_instance.remote_pass_common_class('localhost:5001', date)
        self.assertEqual(ret[0], date.year)
        self.assertEqual(ret[1], date.month)
        self.assertEqual(ret[2], date.day)
        self.assertEqual(ret[3], date.hour)
        self.assertEqual(ret[4], date.minute)
        self.assertEqual(ret[5], date.second)
        self.assertEqual(ret[6], date.microsecond)

    def test_pass_custom_class(self):
        dummy = DummyClass(53, 35)
        ret = self.class_instance.remote_pass_custom_class('localhost:5001', dummy)
        self.assertEqual(ret, 88)

    def test_get_class_variables(self):
        ret = self.class_instance.remote_get_class_variables('localhost:5001')
        self.assertTrue(type(ret) == tuple)
        self.assertEqual(ret[0], 'this_is@a#string')
        self.assertEqual(ret[1], 12349 * 2)

    def test_raise_type_error(self):
        with self.assertRaises(TypeError) as error_context:
            self.class_instance.remote_raise_type_error('localhost:5001')
        e = error_context.exception
        self.assertEqual(e.message, '___Failure1')

    def test_raise_custom_error(self):
        with self.assertRaises(remotable_class.ExternalEmptyError) as error_context:
            self.class_instance.remote_raise_custom_error('localhost:5001')
        e = error_context.exception
        self.assertEqual(e.message, '___Failure2')

    def test_create_file(self):
        filename = self.class_instance.remote_create_file('localhost:5001')
        with open(filename) as fin:
            self.assertEqual(fin.read().strip(), self.class_instance.file_contents)
        os.remove(filename)

    def test_call_nested_function(self):
        with self.assertRaises(TypeError) as error_context:
            self.class_instance.remote_call_nested_function('localhost:5001')
        e = error_context.exception
        self.assertEqual(e.message, '___Failure1')

    def test_raise_private_error(self):
        """
        Test how the metaclass deals with exceptions that it cannot reraise. In this case,
        the MyPrivateError exception class is defined within the TestClass, and so it cannot
        be pickled. That means that it cannot be re-raised, and so a JobFailedError should
        be raised instead. However, we can still check that the MyPrivateError exception
        was raised on the server end.
        """
        with self.assertRaises(JobFailedError) as error_context:
            self.class_instance.remote_raise_private_error('localhost:5001')
        e = error_context.exception
        self.assertIn('Root Error Message: ___Failure3', e.__str__())
        match = re.search('Root Error Type: <class \'.*\.MyPrivateError\'>', e.__str__())
        self.assertIsNotNone(match)

    def test_raise_public_error(self):
        with self.assertRaises(remotable_class.ExternalCustomError) as error_context:
            self.class_instance.remote_raise_public_error('localhost:5001')
        self.assertEqual(error_context.exception.message, '___Failure4')

    def test_return_custom_exception(self):
        """
        Tests whether non-trivial class instances can be returned
        """
        ret = self.class_instance.remote_return_custom_exception('localhost:5001')
        self.assertIsInstance(ret, remotable_class.ExternalCustomError)
        self.assertEqual(ret.message, '___Failure4')

    def test_return_none_start_join(self):
        job = self.class_instance.remote_async_return_none('localhost:5001')
        job.start()
        ret = 'something_not_none'
        ret = job.join()
        self.assertIsNone(ret)

    def test_return_number_start_join(self):
        job = self.class_instance.remote_async_return_number('localhost:5001')
        job.start()
        ret = job.join()
        self.assertEqual(ret, 777)

    def test_create_specified_file_start(self):
        # This function is considered unsafe, but it should be fine in this case since there are no security concerns
        filename = tempfile.mktemp()
        job = self.class_instance.remote_async_create_specified_file('localhost:5001', filename, 'specified_contents')
        job.start()
        self.assertFalse(os.path.exists(filename))
        time.sleep(5)  # Give time to create file
        with open(filename) as fin:
            self.assertEqual(fin.read().strip(), 'specified_contents')
        os.remove(filename)
        job.join()

    def test_create_specified_file_default_contents_start(self):
        # This function is considered unsafe, but it should be fine in this case since there are no security concerns
        filename = tempfile.mktemp()
        job = self.class_instance.remote_async_create_specified_file('localhost:5001', filename)
        job.start()
        self.assertFalse(os.path.exists(filename))
        time.sleep(5)  # Give time to create file
        with open(filename) as fin:
            self.assertEqual(fin.read().strip(), 'default_contents')
        os.remove(filename)
        job.join()

    def test_derived_class(self):
        """
        Tests that the remotify decorator works properly when applied to classes which use inheritance
        """
        child_class_instance = remotable_class.ChildClass(30, 15)
        child_class_members = dir(child_class_instance)

        grandchild_class_instance = remotable_class.GrandchildClass(45, 30, 15)
        grandchild_class_members = dir(grandchild_class_instance)

        self.assertIn('remote_func_1', child_class_members)
        self.assertIn('remote_func_2', child_class_members)
        self.assertIn('remote_func_3', child_class_members)
        self.assertIn('remote_func_4', child_class_members)
        self.assertIn('remote_async_func_1', child_class_members)
        self.assertIn('remote_async_func_2', child_class_members)
        self.assertIn('remote_async_func_3', child_class_members)
        self.assertIn('remote_async_func_4', child_class_members)

        self.assertNotIn('remote_func_5', grandchild_class_members)
        self.assertNotIn('remote_func_6', grandchild_class_members)
        self.assertNotIn('remote_async_func_5', grandchild_class_members)
        self.assertNotIn('remote_async_func_6', grandchild_class_members)
        self.assertIn('func_1', grandchild_class_members)
        self.assertIn('func_2', grandchild_class_members)
        self.assertIn('func_3', grandchild_class_members)
        self.assertIn('func_4', grandchild_class_members)
        self.assertIn('remote_func_1', grandchild_class_members)
        self.assertIn('remote_func_2', grandchild_class_members)
        self.assertIn('remote_func_3', grandchild_class_members)
        self.assertIn('remote_func_4', grandchild_class_members)
        self.assertIn('remote_async_func_1', grandchild_class_members)
        self.assertIn('remote_async_func_2', grandchild_class_members)
        self.assertIn('remote_async_func_3', grandchild_class_members)
        self.assertIn('remote_async_func_4', grandchild_class_members)

        time.sleep(1)  # Extra delay, since this test seems sporadic
        self.assertEqual(child_class_instance.remote_func_3('localhost:5001', 3), 3 + 3 + 15 + 30)
        self.assertEqual(child_class_instance.remote_func_4('localhost:5001', 6), 4 + 6 + 15 + 30)
        self.assertEqual(grandchild_class_instance.remote_func_3('localhost:5001', 9), 3 + 9 + 15 + 30)
        self.assertEqual(grandchild_class_instance.remote_func_4('localhost:5001', 12), 4 + 12 + 15 + 30)


    def test_job_timeout(self):
        with self.assertRaises(TimeoutError):
            self.class_instance.remote_long_job('localhost:5001', remote_timeout=3)

    def test_job_does_not_timeout(self):
        self.class_instance.remote_long_job('localhost:5001', remote_timeout=12)

    def test_async_job_timeout(self):
        with self.assertRaises(TimeoutError):
            job = self.class_instance.remote_async_long_job('localhost:5001')
            job.start()
            job.join(3)

    def test_async_job_does_not_timeout(self):
        job = self.class_instance.remote_async_long_job('localhost:5001')
        job.start()
        job.join(12)

    ''' Still need to add support for static functions - may need to write another Hoplite plugin to handle them
    def test_call_static_function(self):
        ret = remotable_class.TestClass.remote_static_return_number('localhost:5001')
        self.assertEqual(ret, 999)
    '''


class TestRemotableModuleCapabilities(unittest2.TestCase):
    def setUp(self):
        self.proc = start_hoplite_server(5001)
        self.manager = RemoteJobManager("localhost", 5001)

    def tearDown(self):
        tear_down_hoplite(self.proc)
        time.sleep(.5)

    def test_return_none(self):
        ret = remotable_module.remote_return_none('localhost:5001')
        self.assertIsNone(ret)

    def test_return_number(self):
        ret = remotable_module.remote_return_number('localhost:5001')
        self.assertEqual(ret, 777)

    def test_return_tuple(self):
        ret = remotable_module.remote_return_tuple('localhost:5001')
        self.assertTrue(type(ret) == tuple)
        self.assertTupleEqual(ret, ('All', 4, 1.11))

    def test_return_list(self):
        ret = remotable_module.remote_return_single_list('localhost:5001')
        self.assertTrue(type(ret) == list)
        self.assertListEqual(ret, ['This', 'is', 'a', 'list'])

    def test_return_multiple_lists(self):
        ret = remotable_module.remote_return_multiple_lists('localhost:5001')
        self.assertTrue(type(ret) == tuple)
        self.assertListEqual(ret[0], ['This', 'is', 1, 'list'])
        self.assertListEqual(ret[1], ['and', 'this', 'is', 'another', 'list'])

    def test_do_math(self):
        ret = remotable_module.remote_do_math('localhost:5001', 17, 13.5)
        self.assertEqual(ret, 17 * 13.5)

    def test_pass_common_class(self):
        date = datetime.datetime.now()
        ret = remotable_module.remote_pass_common_class('localhost:5001', date)
        self.assertEqual(ret[0], date.year)
        self.assertEqual(ret[1], date.month)
        self.assertEqual(ret[2], date.day)
        self.assertEqual(ret[3], date.hour)
        self.assertEqual(ret[4], date.minute)
        self.assertEqual(ret[5], date.second)
        self.assertEqual(ret[6], date.microsecond)

    def test_pass_custom_class(self):
        dummy = DummyClass(53, 35)
        ret = remotable_module.remote_pass_custom_class('localhost:5001', dummy)
        self.assertEqual(ret, 88)

    def test_raise_type_error(self):
        with self.assertRaises(TypeError) as error_context:
            remotable_module.remote_raise_type_error('localhost:5001')
        e = error_context.exception
        self.assertEqual(e.message, '___Failure1')

    def test_raise_custom_error(self):
        with self.assertRaises(remotable_module.ExternalEmptyError) as error_context:
            remotable_module.remote_raise_custom_error('localhost:5001')
        e = error_context.exception
        self.assertEqual(e.message, '___Failure2')

    def test_call_nested_function(self):
        with self.assertRaises(TypeError) as error_context:
            remotable_module.remote_call_nested_function('localhost:5001')
        e = error_context.exception
        self.assertEqual(e.message, '___Failure1')

    def test_raise_private_error(self):
        """
        Test how the metaclass deals with exceptions that it cannot reraise. In this case,
        the MyPrivateError exception class is defined within the TestClass, and so it cannot
        be pickled. That means that it cannot be re-raised, and so a JobFailedError should
        be raised instead. However, we can still check that the MyPrivateError exception
        was raised on the server end.
        """
        with self.assertRaises(JobFailedError) as error_context:
            remotable_module.remote_raise_private_error('localhost:5001')
        e = error_context.exception
        self.assertIn('Root Error Message: ___Failure3', e.__str__())
        match = re.search('Root Error Type: <class \'.*\.MyPrivateError\'>', e.__str__())
        self.assertIsNotNone(match)

    def test_raise_public_error(self):
        with self.assertRaises(remotable_class.ExternalCustomError) as error_context:
            remotable_module.remote_raise_public_error('localhost:5001')
        self.assertEqual(error_context.exception.message, '___Failure4')

    def test_return_custom_exception(self):
        """
        Tests whether non-trivial class instances (such as exceptions) can be returned
        """
        ret = remotable_module.remote_return_custom_exception('localhost:5001')
        self.assertIsInstance(ret, remotable_class.ExternalCustomError)
        self.assertEqual(ret.message, '___Failure4')

    def test_return_none_start_join(self):
        job = remotable_module.remote_async_return_none('localhost:5001')
        job.start()
        ret = 'something_not_none'
        ret = job.join()
        self.assertIsNone(ret)

    def test_return_number_start_join(self):
        job = remotable_module.remote_async_return_number('localhost:5001')
        job.start()
        ret = job.join()
        self.assertEqual(ret, 777)

    def test_create_specified_file_start(self):
        # This function is considered unsafe, but it should be fine in this case since there are no security concerns
        filename = tempfile.mktemp()
        job = remotable_module.remote_async_create_specified_file('localhost:5001', filename, 'specified_contents')
        job.start()
        self.assertFalse(os.path.exists(filename))
        time.sleep(3)  # Give time to create file
        with open(filename) as fin:
            self.assertEqual(fin.read().strip(), 'specified_contents')
        os.remove(filename)
        job.join()

    def test_create_specified_file_default_contents_start(self):
        # This function is considered unsafe, but it should be fine in this case since there are no security concerns
        filename = tempfile.mktemp()
        job = remotable_module.remote_async_create_specified_file('localhost:5001', filename)
        job.start()
        self.assertFalse(os.path.exists(filename))
        time.sleep(3)  # Give time to create file
        with open(filename) as fin:
            self.assertEqual(fin.read().strip(), 'default_contents')
        os.remove(filename)
        job.join()

    def test_job_timeout(self):
        with self.assertRaises(TimeoutError):
            remotable_module.remote_long_job('localhost:5001', remote_timeout=3)

    def test_job_does_not_timeout(self):
        remotable_module.remote_long_job('localhost:5001', remote_timeout=12)

    def test_async_job_timeout(self):
        with self.assertRaises(TimeoutError):
            job = remotable_module.remote_async_long_job('localhost:5001')
            job.start()
            job.join(3)

    def test_async_job_does_not_timeout(self):
        job = remotable_module.remote_async_long_job('localhost:5001')
        job.start()
        job.join(12)


class TestRemotableClassClientLogging(unittest2.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('hoplite.remote_enabler')
        self.logger_path = tempfile.mktemp()
        self.logger_handler = logging.FileHandler(self.logger_path)
        self.logger.addHandler(self.logger_handler)
        self.logger.setLevel(logging.DEBUG)

        self.proc = start_hoplite_server(5001)
        self.manager = RemoteJobManager("localhost", 5001)
        self.class_instance = remotable_class.TestClass('this_is@a#string', 12349)

    def tearDown(self):
        tear_down_hoplite(self.proc)
        self.logger_handler.close()
        self.logger.removeHandler(self.logger_handler)

    def test_logging__remote_func(self):
        ret = self.class_instance.remote_do_math('localhost:5001', 2, 3)
        self.assertEqual(ret, 6)

        with open(self.logger_path) as fin:
            all_lines = fin.readlines()
        self.assertEqual(all_lines[0].strip(), '"{0}" on target "{1}" with args: {2} and kwargs: {3}'.format(
            'do_math', 'localhost:5001', (2, 3), {}))
        self.assertEqual(all_lines[1].strip(), '"{0}" on target "{1}" returned {2}'.format('do_math', 'localhost:5001', 6))

    def test_logging__remote_async_func(self):
        job = self.class_instance.remote_async_do_math('localhost:5001', 2, 3)
        job.start()
        ret = job.join()

        self.assertEqual(ret, 6)

        with open(self.logger_path) as fin:
            all_lines = fin.readlines()

        self.assertEqual(all_lines[0].strip(), 'Creating job "{0}" on target "{1}" with args: {2} and kwargs: {3}'.format(
            'do_math', 'localhost:5001', (2, 3), {}))
        self.assertIsNotNone(r'Starting "do_math\(.*\)" on "localhost:5001"', all_lines[1].strip())
        self.assertEqual(all_lines[2].strip(), 'Joining "{0}" on "{1}"'.format('do_math', 'localhost:5001'))
        self.assertEqual(all_lines[3].strip(), '"{0}" on target "{1}" returned {2}'.format(
            'do_math', 'localhost:5001', 6))


class TestRemotableModuleClientLogging(unittest2.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('hoplite.remote_enabler')
        self.logger_path = tempfile.mktemp()
        self.logger_handler = logging.FileHandler(self.logger_path)
        self.logger.addHandler(self.logger_handler)
        self.logger.setLevel(logging.DEBUG)

        self.proc = start_hoplite_server(5001)
        self.manager = RemoteJobManager("localhost", 5001)

    def tearDown(self):
        tear_down_hoplite(self.proc)
        self.logger_handler.close()
        self.logger.removeHandler(self.logger_handler)

    def test_logging__remote_module_func(self):
        ret = remotable_module.remote_do_math('localhost:5001', 2, 3)
        self.assertEqual(ret, 6)

        with open(self.logger_path) as fin:
            all_lines = fin.readlines()
        self.assertEqual(all_lines[0].strip(), '"{0}" on target "{1}" with args: {2} and kwargs: {3}'.format(
            'do_math', 'localhost:5001', (2, 3), {}))
        self.assertEqual(all_lines[1].strip(), '"{0}" on target "{1}" returned {2}'.format('do_math', 'localhost:5001', 6))

    def test_logging__remote_module_async_func(self):
        job = remotable_module.remote_async_do_math('localhost:5001', 2, 3)
        job.start()
        ret = job.join()

        self.assertEqual(ret, 6)

        with open(self.logger_path) as fin:
            all_lines = fin.readlines()
        self.assertEqual(all_lines[0].strip(), 'Creating job "{0}" on target "{1}" with args: {2} and kwargs: {3}'.format(
            'do_math', 'localhost:5001', (2, 3), {}))
        self.assertIsNotNone(r'Starting "do_math\(.*\)" on "localhost:5001"', all_lines[1].strip())
        self.assertEqual(all_lines[2].strip(), 'Joining "{0}" on "{1}"'.format('do_math', 'localhost:5001'))
        self.assertEqual(all_lines[3].strip(), '"{0}" on target "{1}" returned {2}'.format(
            'do_math', 'localhost:5001', 6))


class TestRemotableClassServerLogging(unittest2.TestCase):
    def setUp(self):
        self.proc = start_hoplite_server(5001)
        self.manager = RemoteJobManager("localhost", 5001)
        self.class_instance = remotable_class.TestClass('this_is@a#string', 12349)

    def tearDown(self):
        tear_down_hoplite(self.proc)

    def test_logging_log_normal(self):
        rand_string_1 = get_random_string(5, 10)
        rand_string_2 = get_random_string(5, 10)
        log_folder = r'C:\logs\hoplite\remoted_functions\tests\remotable_test_resources\remotable_class\TestClass'
        ret = self.class_instance.remote_log_normal('localhost:5001', rand_string_1, dummy_var_2=rand_string_2)
        latest_log_file = max(
            [os.path.join(log_folder, filename) for filename in os.listdir(log_folder)], key=os.path.getctime
        )
        self.assertEqual(ret, '{} + {}'.format(rand_string_1, rand_string_2))
        with open(os.path.join(log_folder, latest_log_file)) as fin:
            all_lines = fin.readlines()
        self.assertEqual(len(all_lines), 3)
        self.assertIn("Beginning execution of log_normal with args: ('{}',) and kwargs: {{'dummy_var_2': '{}'}}".format(
            rand_string_1, rand_string_2), all_lines[0]
        )
        self.assertIn('Logging in log_normal function', all_lines[1])
        self.assertIn(
            'Returning from log_normal with return value(s): {} + {}'.format(rand_string_1, rand_string_2), all_lines[2]
        )
        os.remove(latest_log_file)

    def test_logging_log_exception(self):
        log_folder = r'C:\logs\hoplite\remoted_functions\tests\remotable_test_resources\remotable_class\TestClass'
        with self.assertRaises(TypeError) as error_context:
            self.class_instance.remote_raise_type_error('localhost:5001')
        self.assertEqual(error_context.exception.message, '___Failure1')

        latest_log_file = max(
            [os.path.join(log_folder, filename) for filename in os.listdir(log_folder)], key=os.path.getctime
        )
        with open(os.path.join(log_folder, latest_log_file)) as fin:
            all_lines = fin.readlines()
        self.assertEqual(len(all_lines), 8)
        self.assertIn('Beginning execution of raise_type_error with args: () and kwargs: {}', all_lines[0])
        self.assertIn('An exception occurred', all_lines[1])
        self.assertIn('Traceback', all_lines[2])
        self.assertIn('in run', all_lines[3])
        self.assertIn('TypeError: ___Failure1', all_lines[7])
        os.remove(latest_log_file)

    def test_logging_nested_logs(self):
        log_folder = r'C:\logs\hoplite\remoted_functions\tests\remotable_test_resources\remotable_class\TestClass'
        self.class_instance.remote_log_nested_caller('localhost:5001')

        latest_log_file = max(
            [os.path.join(log_folder, filename) for filename in os.listdir(log_folder)], key=os.path.getctime
        )
        with open(os.path.join(log_folder, latest_log_file)) as fin:
            all_lines = fin.readlines()
        self.assertEqual(len(all_lines), 4)
        self.assertIn('Currently in class caller function', all_lines[1])
        self.assertIn('Currently in class callee function', all_lines[2])
        os.remove(latest_log_file)


class TestRemotableModuleServerLogging(unittest2.TestCase):
    def setUp(self):
        self.proc = start_hoplite_server(5001)
        self.manager = RemoteJobManager("localhost", 5001)

    def tearDown(self):
        tear_down_hoplite(self.proc)

    def test_logging_log_normal(self):
        rand_string_1 = get_random_string(5, 10)
        rand_string_2 = get_random_string(5, 10)
        log_folder = r'C:\logs\hoplite\remoted_functions\tests\remotable_test_resources\remotable_module'
        ret = remotable_module.remote_log_normal('localhost:5001', rand_string_1, dummy_var_2=rand_string_2)
        latest_log_file = max(
            [os.path.join(log_folder, filename) for filename in os.listdir(log_folder)], key=os.path.getctime
        )
        self.assertEqual(ret, '{} + {}'.format(rand_string_1, rand_string_2))
        with open(os.path.join(log_folder, latest_log_file)) as fin:
            all_lines = fin.readlines()
        self.assertEqual(len(all_lines), 3)
        self.assertIn("Beginning execution of log_normal with args: ('{}',) and kwargs: {{'dummy_var_2': '{}'}}".format(
            rand_string_1, rand_string_2), all_lines[0]
        )
        self.assertIn('Logging in log_normal function', all_lines[1])
        self.assertIn(
            'Returning from log_normal with return value(s): {} + {}'.format(rand_string_1, rand_string_2), all_lines[2]
        )
        os.remove(latest_log_file)

    def test_logging_log_exception(self):
        log_folder = r'C:\logs\hoplite\remoted_functions\tests\remotable_test_resources\remotable_module'
        with self.assertRaises(TypeError) as error_context:
            remotable_module.remote_raise_type_error('localhost:5001')
        self.assertEqual(error_context.exception.message, '___Failure1')

        latest_log_file = max(
            [os.path.join(log_folder, filename) for filename in os.listdir(log_folder)], key=os.path.getctime
        )
        with open(os.path.join(log_folder, latest_log_file)) as fin:
            all_lines = fin.readlines()
        self.assertEqual(len(all_lines), 8)
        self.assertIn('Beginning execution of raise_type_error with args: () and kwargs: {}', all_lines[0])
        self.assertIn('An exception occurred', all_lines[1])
        self.assertIn('Traceback', all_lines[2])
        self.assertIn('in run', all_lines[3])
        self.assertIn('TypeError: ___Failure1', all_lines[7])
        os.remove(latest_log_file)

    def test_logging_nested_logs(self):
        log_folder = r'C:\logs\hoplite\remoted_functions\tests\remotable_test_resources\remotable_module'
        remotable_module.remote_log_nested_caller('localhost:5001')

        latest_log_file = max(
            [os.path.join(log_folder, filename) for filename in os.listdir(log_folder)], key=os.path.getctime
        )
        with open(os.path.join(log_folder, latest_log_file)) as fin:
            all_lines = fin.readlines()
        self.assertEqual(len(all_lines), 4)
        self.assertIn('Currently in caller function', all_lines[1])
        self.assertIn('Currently in callee function', all_lines[2])
        os.remove(latest_log_file)


def get_random_string(min_length, max_length):
    return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits)
                   for _ in range(random.randint(min_length, max_length)))