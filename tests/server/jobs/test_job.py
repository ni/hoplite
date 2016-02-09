import time

from hoplite.builtin_plugins.constants import DOWNLOAD_NETWORK_FOLDER_JOB_NAME
from hoplite.utils import server_logging
from hoplite.server.jobs.job import Job, JobNotStartedError, NotAuthorizedError
from tests import HopliteTestCase

logger = server_logging.get_server_logger(__name__)


class TestJob(HopliteTestCase):
    def setUp(self):
        super(TestJob, self).setUp()
        self.job = Job("{3939}", DOWNLOAD_NETWORK_FOLDER_JOB_NAME, { "path": "/path/to/something" }, "temp")

    def test_initialize(self):
        self.assertEquals(self.job.uuid, "{3939}")
        self.assertEquals(self.job.name, DOWNLOAD_NETWORK_FOLDER_JOB_NAME)
        self.assertEquals(self.job.config, { "path": "/path/to/something" })
        self.assertEquals(self.job.running(), False)

    def test_start(self):
        self.job.start()
        self.assertTrue(self.job.running())
        self.job.kill()

    def test_finished_throws_if_job_not_started(self):
        with self.assertRaises(JobNotStartedError):
            self.job.finished()

    def test_finished(self):
        job = Job("No ID", self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME, { "No": "Config" }, "some_complex_key")
        job.start()
        while job.running():
            pass
        self.assertTrue(job.finished())

    def test_to_dict(self):
        d = self.job.to_dict()
        self.assertEquals(d["uuid"], "{3939}")
        self.assertEquals(d["name"], DOWNLOAD_NETWORK_FOLDER_JOB_NAME)
        self.assertEquals(d["config"], { "path": "/path/to/something" })
        self.assertEquals(d["status"], {})
        self.assertFalse(d["running"])
        self.assertFalse(d["finished"])

    def test_returns_exception_information_in_status(self):
        config = {}
        job = Job("666", self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME, config, "api_key", entry_point_group_name='hoplite.test_jobs')
        job.start()
        while job.running():
            time.sleep(.01)
        exc_info = job.status()["exception"]
        traceback = None
        # Get to the bottom level of the exception information
        while ('type' not in exc_info) and (exc_info is not None):
            traceback = exc_info.get("traceback", None)
            exc_info = exc_info.get('previous_exception', None)
        self.maxDiff = None
        self.assertEqual(exc_info["type"], str(TypeError))
        self.assertEqual(exc_info["message"], "THE SKY IS FALLING!!")
        self.assertIsNotNone(traceback)

    def test_returns_status(self):
        self.assertEqual(self.job.status(), {})

    def test_updates_status(self):
        self.job.update_status(self.job._api_key, { "slave_ip": "10.2.13.123" })
        status = self.job.status()
        self.assertEquals(status, { "slave_ip": "10.2.13.123" })
        # Make sure it overwrites old key values
        self.job.update_status(self.job._api_key, { "slave_ip": "12.3.4.567" })
        status = self.job.status()
        self.assertEquals(status, { "slave_ip": "12.3.4.567" })

    def test_update_status_raises_on_invalid_api_key(self):
        self.assertRaises(NotAuthorizedError, self.job.update_status, "", {"Not": "Authorized"})

    def test_kill(self):
        job = Job("No ID", self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, { "No": "Config" }, "temp_api_key")
        logger.info("Starting job")
        job.start()
        self.assertTrue(job.running())
        job.kill()
        start_time = time.time()
        while job.running():
            if time.time() - start_time > 1:
                raise Exception("Job not killed in time")
        self.assertTrue(job.finished())
