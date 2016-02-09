from httmock import urlmatch, HTTMock, response, all_requests
import psutil
import sys
import time
import unittest2

from hoplite.builtin_plugins.constants import DOWNLOAD_NETWORK_FOLDER_JOB_NAME, DOWNLOAD_FOLDER_FROM_FTP_JOB_NAME
from hoplite.client.remote_job_manager import RemoteJobManager
from hoplite.exceptions import InternalServerError
from hoplite.public_api import wait_for_hoplite
from hoplite.serializer import hoplite_dumps
from hoplite.server.jobs.job_manager import JobDoesNotExistError
from hoplite.utils import server_logging

logger = server_logging.get_server_logger(__name__)


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


@urlmatch(netloc="localhost:5001", path='\/jobs\/running')
def get_running_jobs(url, request):
    if request.method == 'GET':
        return response(200, hoplite_dumps({"jobs": [{"uuid": 111}]}))

@all_requests
def response_500(url, request):
    return response(500)

class TestRemoteDaemonManager(unittest2.TestCase):
    def setUp(self):
        self.proc = start_hoplite_server(5001)
        self.manager = RemoteJobManager("localhost", 5001)

    def tearDown(self):
        tear_down_hoplite(self.proc)

    def test_create_job(self):
        job = None
        job = self.manager.create_job(DOWNLOAD_NETWORK_FOLDER_JOB_NAME, {})
        self.assertIsNotNone(job)
        self.assertEquals(job.name, DOWNLOAD_NETWORK_FOLDER_JOB_NAME)
        self.assertEquals(job.running(), False)

    def test_get_job(self):
        job = self.manager.create_job(DOWNLOAD_NETWORK_FOLDER_JOB_NAME, {})
        r_job = self.manager.get_job(job.uuid)
        self.assertEquals(r_job.uuid, job.uuid)
        self.assertEquals(r_job.name, job.name)

    def test_get_job_raises(self):
        self.assertRaises(JobDoesNotExistError, self.manager.get_job, 393939)

    def test_get_job_plugins(self):
        job_plugins = self.manager.get_job_plugins()
        self.assertEquals(len(job_plugins), 7)
        actual = job_plugins
        self.assertIn(DOWNLOAD_FOLDER_FROM_FTP_JOB_NAME, actual)
        self.assertIn(DOWNLOAD_NETWORK_FOLDER_JOB_NAME, actual)

    def test_get_job_plugins_raises(self):
        with HTTMock(response_500):
            self.assertRaises(InternalServerError, self.manager.get_job_plugins)

    def test_get_running_jobs(self):
        jobs = self.manager.get_running_jobs()
        self.assertEqual(len(jobs), 0)
        with HTTMock(get_running_jobs):
            jobs = self.manager.get_running_jobs()
            self.assertEqual(len(jobs), 1)

    def test_reload_site_packages(self):
        done = self.manager.reload_site_packages()
        self.assertTrue(done)

    def test_is_manager_available(self):
        time.sleep(1)  # Give some time for job manager to connect to start
        self.assertTrue(self.manager.is_available())
        invalid_manager = RemoteJobManager("localhost", 48423)
        self.assertFalse(invalid_manager.is_available())