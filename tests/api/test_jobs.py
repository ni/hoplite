from hoplite.utils import server_logging
from tests.api import HopliteApiTestCase
from flask import json
from hoplite.api.helpers import job_manager
import time

logger = server_logging.get_server_logger(__name__)


class JobsApiTestCase(HopliteApiTestCase):
    def setUp(self):
        super(JobsApiTestCase, self).setUp()
        self.manager = job_manager

    def test_get_jobs(self):
        self.manager.create_job(self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, {})
        self.manager.create_job(self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME, {})
        r = self.client.get('/jobs')
        self.assertOk(r)
        job_list = json.loads(r.get_data())["jobs"]
        print job_list
        self.assertEquals(len(job_list), 2)
        # Get names from 3 jobs then sort and compare
        names = []
        for job in job_list:
            names.append(job["name"])
        expected = [self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME,
                    self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME]
        self.assertEquals(sorted(names), sorted(expected))

    def test_post_jobs_blank_config(self):
        data = {"name": self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME}
        r = self.jpost('/jobs', data=data)
        self.assertOk(r)
        r_job = json.loads(r.get_data())
        self.assertEquals(data["name"], r_job["name"])
        self.assertEquals(r_job["config"], {})
        self.assertEquals(r_job["running"], False)

    def test_post_jobs_config(self):
        data = {"name": self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, "config": { "something": "yay" }}
        r = self.jpost('/jobs', data=data)
        self.assertOk(r)
        r_job = json.loads(r.get_data())
        self.assertEquals(data["name"], r_job["name"])
        self.assertEquals(data["config"], r_job["config"])
        self.assertEquals(r_job["running"], False)

    def test_post_jobs_running_true(self):
        data = {"name": self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, "running": True}
        r = self.jpost('/jobs', data=data)
        self.assertOk(r)
        r_job = json.loads(r.get_data())
        self.assertEquals(data["name"], r_job["name"])
        self.assertEquals(r_job["config"], {})
        self.assertEquals(r_job["running"], True)
        self._terminate_all_jobs()

    def test_post_job_bad_name_returns_400(self):
        data = {"name": "Bad Name", "config": { "something": "yay" }}
        r = self.jpost('/jobs', data=data)
        self.assertBadRequest(r)
        self.assertEquals(json.loads(r.get_data())["error"], "Job plugin 'Bad Name' does not exist")

    def test_put_job_updates_status(self):
        job = self._create_job()
        status_update = { "status": { "my_status": "is good" }, "api_key": job._api_key}
        r = self.jput("/jobs/{0}".format(job.uuid), data=status_update)
        self.assertEquals(job.status(), { "my_status": "is good" })

    def test_get_jobs_running(self):
        e_job_uuid = []
        jobs = []
        print self.manager.available_job_plugins()
        for i in range(4):
            job = self.manager.create_job(self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, {}, True)
            jobs.append(job)
            e_job_uuid.append(job.uuid)
        print jobs[0].status()
        r = self.client.get('/jobs/running')
        self.assertOk(r)
        r_jobs = json.loads(r.get_data())["jobs"]
        self.assertEquals(len(r_jobs), 4)
        r_job_uuid = []
        for job in r_jobs:
            r_job_uuid.append(job["uuid"])
        self.assertEquals(sorted(e_job_uuid), sorted(r_job_uuid))
        self._terminate_all_jobs()

    def test_put_start_job(self):
        job = self.manager.create_job(self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, {})
        self.assertFalse(job.running())
        r = self.client.put('/jobs/{0}/start'.format(job.uuid))
        self.assertOk(r)
        r_body = json.loads(r.get_data())
        self.assertTrue(r_body["started"])
        self.assertEquals(r_body["uuid"], job.uuid)
        self.assertTrue(job.running())
        self._terminate_all_jobs()

    def test_put_start_job_error_if_job_finished(self):
        job = self._create_job(self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME, running=True)
        while job.running():
            pass
        r = self.client.put('/jobs/{0}/start'.format(job.uuid))
        self.assertForbidden(r)
        r_body = json.loads(r.get_data())
        self.assertEquals(r_body["error"], "Job UUID: {0} you cannot start a job more than once".format(job.uuid))

    def test_put_start_job_job_already_started(self):
        job = self._create_job(running=True)
        self.assertTrue(job.running())
        r = self.client.put('/jobs/{0}/start'.format(job.uuid))
        self.assertForbidden(r)
        r_body = json.loads(r.get_data())
        self.assertEquals(r_body["error"], "Job UUID: {0} you cannot start a job more than once".format(job.uuid))
        self._terminate_all_jobs()

    def test_put_start_job_error_if_job_does_not_exist(self):
        r = self.client.put('/jobs/{0}/start'.format(3288283))
        self.assertNotFound(r)
        r_body = json.loads(r.get_data())
        self.assertEquals(r_body["error"], "Job with UUID: 3288283 does not exist")

    def test_put_kill_job_error_if_job_finished(self):
        job = self._create_job(self.test_jobs_module.constants.THROW_AN_EXCEPTION_JOB_NAME, running=True)
        while job.running():
            pass
        r = self.client.put('/jobs/{0}/kill'.format(job.uuid))
        self.assertOk(r)
        r_body = json.loads(r.get_data())

    def test_put_kill_job_error_if_job_not_started(self):
        job = self._create_job()
        r = self.client.put('/jobs/{0}/kill'.format(job.uuid))
        self.assertForbidden(r)
        r_body = json.loads(r.get_data())
        self.assertEquals(r_body["error"], "Job UUID: {0} has not been started".format(job.uuid))

    def test_put_kill_job_error_if_job_does_not_exist(self):
        r = self.client.put('/jobs/{0}/kill'.format(12312))
        self.assertNotFound(r)
        r_body = json.loads(r.get_data())
        self.assertEquals(r_body["error"], "Job with UUID: 12312 does not exist")

    def test_put_kill_job(self):
        job = self.manager.create_job(self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME, {}, True)
        self.assertTrue(job.running())
        r = self.client.put('/jobs/{0}/kill'.format(job.uuid))
        self.assertOk(r)
        r_body = json.loads(r.get_data())
        self.assertTrue(r_body["killed"])
        self.assertEquals(r_body["uuid"], job.uuid)
        start_time = time.time()
        while job.running():
            elapsed_time = time.time() - start_time
            if elapsed_time > 5:
                self.fail("Timed out waiting for job to die")
        self.assertTrue(job.finished())

    def test_get_jobs_uuid(self):
        job = self._create_job()
        r = self.client.get('/jobs/{0}'.format(job.uuid))
        self.assertOk(r)
        r_job = json.loads(r.get_data())
        self.assertEquals(r_job["uuid"], job.uuid)
        self.assertEquals(r_job["name"], self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME)
        self.assertFalse(r_job["running"])
        self.assertFalse(r_job["finished"])
        self.assertFalse(r_job["killed"])
        logger.info("Starting job")
        job.start()
        r = self.client.get('/jobs/{0}'.format(job.uuid))
        self.assertOk(r)
        r_job = json.loads(r.get_data())
        self.assertTrue(r_job["running"])
        self.assertFalse(r_job["finished"])
        self.assertFalse(r_job["killed"])
        self._terminate_all_jobs()
        while job.running():
            pass
        r = self.client.get('/jobs/{0}'.format(job.uuid))
        self.assertOk(r)
        r_job = json.loads(r.get_data())
        self.assertFalse(r_job["running"])
        self.assertTrue(r_job["finished"])
        self.assertTrue(r_job["killed"])

    def test_get_jobs_uuid_with_bad_id(self):
        r = self.client.get('/jobs/{0}'.format("8b7fea59-2c0d-4afa-8109-2bc0a26ec865"))
        self.assertNotFound(r)
        self.assertEquals(json.loads(r.get_data())["error"], "Job with UUID: 8b7fea59-2c0d-4afa-8109-2bc0a26ec865 does not exist")

    def _create_job(self, name=None, config={}, running=False):
        if name is None:
            name = self.test_jobs_module.constants.WAIT_10_SECONDS_JOB_NAME
        return self.manager.create_job(name, config, running, port=5001)

    def _terminate_all_jobs(self):
        jobs = self.manager.all_jobs()
        for job in jobs:
            job.kill()
