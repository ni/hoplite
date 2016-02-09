from hoplite.utils import server_logging

logger = server_logging.get_server_logger(__name__)
from hoplite.server.jobs.job_manager import JobManager
from hoplite.plugin_manager import EntryPointManager
from hoplite.exceptions import JobPluginDoesNotExistError, JobDoesNotExistError
from tests import HopliteTestCase


class TestJobManager(HopliteTestCase):
    def setUp(self):
        super(TestJobManager, self).setUp()
        self.manager = JobManager(EntryPointManager('hoplite.test_jobs'))

    def test_available_jobs(self):
        job_list = self.manager.available_job_plugins()
        self.assertEquals(len(job_list), 4)
        expected = [self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME,
                    self.test_jobs_module.constants.CREATE_FILE_JOB_NAME,
                    self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME,
                    self.test_jobs_module.constants.JOB_FAILED_EXCEPTION_JOB_NAME]
        self.assertEquals(sorted(job_list), sorted(expected))

    def test_job_info_raises_on_invalid_id(self):
        # Rases an exception when passed a bad job id
        self.assertRaises(JobDoesNotExistError, self.manager.get_job, 1)

    def test_job_info_gets_correct_job(self):
        job = self.manager.create_job(self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, {}, port=5001)
        job_2 = self.manager.get_job(job.uuid)
        self.assertEquals(job, job_2)

    def test_create_job_raises_on_invalid_job_plugin_name(self):
        with self.assertRaises(JobPluginDoesNotExistError):
            self.manager.create_job("Fake Job Name", {}, port=5001)

    def test_create_job_running_false(self):
        job = self.manager.create_job(self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME, {}, port=5001)
        self.assertIsNotNone(job.uuid)
        self.assertFalse(job.running())

    def test_create_job_running_true_runs_job(self):
        job = self.manager.create_job(self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, {}, True, port=5001)
        self.assertIsNotNone(job.uuid)
        self.assertTrue(job.running())
        job.kill()