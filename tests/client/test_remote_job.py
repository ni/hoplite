import bson
import datetime
from httmock import urlmatch, HTTMock, response
import pickle
import re
import sys
from tblib import pickling_support
import unittest2

from hoplite.client.remote_job import RemoteJob
from hoplite.exceptions import JobFailedError, JobDoesNotExistError, TimeoutError, ConnectionError
from hoplite.utils import server_logging
from hoplite.serializer import hoplite_dumps

# This makes it so that traceback objects can be pickled
pickling_support.install()

logger = server_logging.get_server_logger(__name__)


# Get an arbitrary traceback object to use for the tests
try:
    raise TypeError()
except:
    pickled_traceback = pickle.dumps(sys.exc_info()[2])


job_dict = {
    "uuid": "correctuuid",
    "name": "test_plugins.wait_10_seconds",
    "config": {"something": "is missing"},
    "status": {
        "Roger": "Roger what's your status?",
        "anumber": 123,
        "objectid": bson.objectid.ObjectId(),
        "datetime": datetime.datetime.now(),
        "regexp": re.compile("hoplite")
    },
    "running": True,
    "finished": False
}

job_dict_2 = {
    "uuid": "correctuuid",
    "name": "test_plugins.wait_10_seconds",
    "config": {"something": "is missing"},
    "status": {"Roger": "Roger what's your status?"},
    "running": False,
    "finished": True
}

job_dict_name_something = {
    "uuid": "correctuuid",
    "name": "something",
    "config": {"something": "is missing"},
    "status": {"Roger": "Roger what's your status?"},
    "running": True,
    "finished": False
}

started_dict = {
    "uuid": "correctuuid",
    "started": "true"
}

killed_dict = {
    "uuid": "correctuuid",
    "killed": "true"
}

excepted_job = {
    "uuid": 0,
    "name": "Failing Job",
    "status": {
        "exception": {
            "traceback": pickled_traceback,
            "previous_exception": {
                "type": "TypeError",
                "message": "Wrong type",
                "exception_object": 'bla_bla_pickled_object'
            }
        }
    }
}

exception_bubble_up_job = {
    "uuid": 0,
    "name": "Failing Job",
    "status": {
        "exception": {
            "address": "10.2.1.10",
            "uuid": 5,
            "type": "TypeError",
            "message": "Wrong type",
            "traceback": pickled_traceback
        }
    }
}

@urlmatch(path='\/jobs\/\w+$')
def get_with_bubbled_up_exception(url, request):
    return response(200, hoplite_dumps(exception_bubble_up_job), {'content-type': 'application/json'})

@urlmatch(path='\/jobs\/\w+$')
def get_with_exception(url, request):
    return response(200, hoplite_dumps(excepted_job), {'content-type': 'application/json'})

@urlmatch(path='\/jobs\/\w+$')
def get_specific_job(url, request):
    return response(200, hoplite_dumps(job_dict), {'content-type': 'application/json'})

@urlmatch(netloc="localhost:5001", path='\/jobs\/\w+$')
def get_specific_job_404(url, request):
    return response(404)

@urlmatch(path='/jobs$')
def post_jobs(url, request):
    if request.method == 'POST' and request.headers['Content-type'] == 'application/json':
        return response(200, hoplite_dumps(job_dict_name_something), {'content-type': 'application/json'})

@urlmatch(path='/jobs$')
def post_jobs_400(url, request):
    if request.method == 'POST' and request.headers['Content-type'] == 'application/json':
        return response(400, hoplite_dumps({"error": "Job not found"}), {'content-type': 'application/json'})

@urlmatch(path='\/jobs\/\w+$')
def get_specific_job_named_something(url, request):
    return response(200, hoplite_dumps(job_dict_name_something), {'content-type': 'application/json'})

@urlmatch(path='\/jobs\/\w+$')
def get_specific_job_running_false_finished_true(url, request):
    return response(200,  hoplite_dumps(job_dict_2), {'content-type': 'application/json'})

@urlmatch(path='\/jobs\/\w+\/start$')
def start_job(url, request):
    if request.method == 'PUT':
        return response(200,  hoplite_dumps(started_dict), {'content-type': 'application/json'})

@urlmatch(path='\/jobs\/\w+\/kill$')
def kill_job(url, request):
    if request.method == 'PUT':
        return response(200,  hoplite_dumps(killed_dict), {'content-type': 'application/json'})


class TestRemoteJob(unittest2.TestCase):
    def setUp(self):
        with HTTMock(get_specific_job):
            self.job = RemoteJob("localhost", 5001, "test_plugins.wait_10_seconds", "correctuuid", "api_key")

    def test_init_addr_name_uuid_apikey(self):
        #TODO There is a testing hole here...Where's config?! Input and Return
        self.assertEquals(self.job.address, "localhost")
        self.assertEquals(self.job.name, "test_plugins.wait_10_seconds")
        self.assertEquals(self.job.uuid, "correctuuid")
        self.assertEquals(self.job._api_key, "api_key")

    def test_init_addr_does_not_exist_raises(self):
        self.assertRaises(
            ConnectionError,
            RemoteJob,
            "localhost.not.the.right.url",
            5001,
            "test_plugins.wait_10_seconds",
            "uuid",
            "api_key"
        )

    def test_init_job_name_does_not_exist_no_uuid_given_raises(self):
        with HTTMock(post_jobs_400):
            self.assertRaises(JobDoesNotExistError, RemoteJob, "localhost", 5001, "test_plugins.wait")

    def test_init_job_no_uuid_given_creates_job(self):
        with HTTMock(post_jobs, get_specific_job_named_something):
            self.job = RemoteJob("localhost", 5001, "something")
        self.assertEquals(self.job.uuid, "correctuuid")
        self.assertEquals(self.job.name, "something")

    def test_config(self):
        with HTTMock(get_specific_job):
            self.assertEquals(self.job.config(), job_dict['config'])

    def test_status(self):
        with HTTMock(get_specific_job):
            self.assertEquals(self.job.status(), job_dict['status'])

    def test_start(self):
        with HTTMock(get_specific_job, start_job):
            self.assertTrue(self.job.start())

    def test_kill(self):
        with HTTMock(get_specific_job, kill_job):
            self.assertTrue(self.job.kill())

    def test_running(self):
        with HTTMock(get_specific_job):
            self.assertTrue(self.job.running())
        with HTTMock(get_specific_job_running_false_finished_true):
            self.assertFalse(self.job.running(force=True))

    def test_finished(self):
        with HTTMock(get_specific_job):
            self.assertFalse(self.job.finished())
        with HTTMock(get_specific_job_running_false_finished_true):
            self.assertTrue(self.job.finished(force=True))

    def test_join(self):
        with HTTMock(get_specific_job_running_false_finished_true):
            self.assertTrue(self.job.join())

    def test_join_raises_timeouteror(self):
        with HTTMock(get_specific_job_named_something):
            self.assertRaises(TimeoutError, self.job.join, 0)

    def test_rate_limit(self):
        with HTTMock(get_specific_job):
            self.assertTrue(self.job.running())
        with HTTMock(get_specific_job_running_false_finished_true):
            self.assertTrue(self.job.running())

    def test_exception_thrown_from_status(self):
        with HTTMock(get_with_exception):
            self.assertRaises(JobFailedError, self.job.status, True)

    def test_exception_thrown_from_join(self):
        with HTTMock(get_with_exception):
            self.assertRaises(JobFailedError, self.job.join)

    def test_exception_thrown_from_status(self):
        with HTTMock(get_with_bubbled_up_exception):
            try:
                self.job.status()
            except JobFailedError as e:
                exception_info = exception_bubble_up_job["status"]["exception"]
                self.assertEqual(e.addr, exception_info["address"])
                self.assertEqual(e.uuid, exception_info["uuid"])
                self.assertEqual(e.type_string, exception_info["type"])
                self.assertEqual(e.msg, exception_info["message"])


