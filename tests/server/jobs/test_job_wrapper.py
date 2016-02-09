import os
import shutil
import types

from hoplite.utils import server_logging
from hoplite.server.jobs.job_wrapper import job_wrapper
from hoplite.client.status_updater import MockStatusUpdater
from multiprocessing import Pipe
import tempfile
from tests import HopliteTestCase

logger = server_logging.get_server_logger(__name__)


class TestJobWrapper(HopliteTestCase):
    def test_job_wrapper_calls_run_on_passed_in_module(self):
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "temp.txt")
        config = { "file_to_create": temp_file }
        module_name = self.test_jobs_module.constants.CREATE_FILE_JOB_NAME
        to_job, to_self = Pipe()
        job_wrapper(to_self, module_name, config, MockStatusUpdater(), entry_point_group_name="hoplite.test_jobs")
        try:
            self.assertTrue(os.path.isfile(temp_file))
        except Exception, e:
            raise e
        finally:
            shutil.rmtree(temp_dir)

    def test_job_wrapper_fills_pipe_with_exception_info(self):
        module_name = self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME
        config = {}
        to_job, to_self = Pipe()
        job_wrapper(to_self, module_name, config, MockStatusUpdater(), entry_point_group_name="hoplite.test_jobs")

        exec_info = to_job.recv()
        # Get to the bottom level of the exception information
        while ('type' not in exec_info) and (exec_info is not None):
            exec_info = exec_info.get('previous_exception', None)
        try:
            self.assertEqual(exec_info['type'], str(TypeError))
            self.assertEqual(exec_info['message'], "THE SKY IS FALLING!!")
        except Exception, e:
            raise e
        finally:
            to_job.close()
            to_self.close()

    def test_job_wrapper_fills_pipe_with_exception_info_bubble_up(self):
        module_name = self.test_jobs_module.constants.JOB_FAILED_EXCEPTION_JOB_NAME
        config = {}
        to_job, to_self = Pipe()
        job_wrapper(to_self, module_name, config, MockStatusUpdater(), entry_point_group_name="hoplite.test_jobs")

        exec_info = to_job.recv()
        exec_info = exec_info.get('previous_exception', None)
        try:
            self.assertEqual(exec_info['address'], "10.2.1.1")
            self.assertEqual(exec_info['uuid'], "5")
            self.assertIsInstance(exec_info['traceback'], types.TracebackType)
            # Get to the very bottom level of the exception information
            exec_info = exec_info.get('previous_exception', None)
            self.assertEqual(exec_info['message'], "Test Message")
            self.assertEqual(exec_info['type'], "Test Type String")
            self.assertEqual(exec_info['exception_object'], "pickled_string")
        except Exception, e:
            raise e
        finally:
            to_job.close()
            to_self.close()