from hoplite.utils import server_logging
from flask import json
from hoplite.api.helpers import job_manager
from . import HopliteApiTestCase

logger = server_logging.get_server_logger(__name__)


class JobPluginsApiTestCase(HopliteApiTestCase):
    def setUp(self):
        super(JobPluginsApiTestCase, self).setUp()
        self.manager = job_manager

    def test_get_job_plugins(self):
        r = self.client.get('/job_plugins')
        # 200 OK
        self.assertOk(r)
        # Test that all test builtin_plugins are returned
        body = json.loads(r.get_data())
        job_plugins = body["job_plugins"]
        self.assertEquals(len(job_plugins), 4)
        expected = [self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME,
                    self.test_jobs_module.constants.CREATE_FILE_JOB_NAME,
                    self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME,
                    self.test_jobs_module.constants.JOB_FAILED_EXCEPTION_JOB_NAME]

        self.assertEquals(sorted(job_plugins), sorted(expected))