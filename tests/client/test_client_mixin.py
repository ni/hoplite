from hoplite.client.helpers import ClientMixin
import unittest2
from hoplite.serializer import hoplite_dumps
from httmock import HTTMock, urlmatch, response, all_requests
from tests.utils import StatusCodeTestMixin
from hoplite.exceptions import InternalServerError

DATA = {"status": "ok"}

def _request_has_json_content_type(request):
    if request.headers['content-type'] == 'application/json':
        return True
    return False

@urlmatch(netloc='localhost:5001', path='\/test$')
def get(url, request):
    if request.method == 'GET':
        return response(200)

@urlmatch(netloc='localhost:5001', path='\/test$')
def post(url, request):
    print request.body
    if request.method == 'POST' and _request_has_json_content_type(request)\
            and request.body == hoplite_dumps(DATA):
        return response(200)

@urlmatch(netloc='localhost:5001', path='\/test$')
def put(url, request):
    if request.method == 'PUT' and _request_has_json_content_type(request)\
            and request.body == hoplite_dumps(DATA):
        return response(200)

@urlmatch(netloc='localhost:5001', path='\/test$')
def patch(url, request):
    if request.method == 'PATCH' and _request_has_json_content_type(request)\
            and request.body == hoplite_dumps(DATA):
        return response(200)

@urlmatch(netloc='localhost:5001', path='\/test$')
def delete(url, request):
    if request.method == 'DELETE' and _request_has_json_content_type(request)\
            and request.body == hoplite_dumps(DATA):
        return response(200)

def return_500(url, request):
    response(500)

class HopliteTestCase(unittest2.TestCase):
    pass

class HopliteClientTestCase(StatusCodeTestMixin, HopliteTestCase):
    pass

class TestClientMixin(HopliteClientTestCase):
    def setUp(self):
        self.mixin = ClientMixin()

    def test_jget(self):
        with HTTMock(get):
            r = self.mixin.jget("http://localhost:5001/test")
            self.assertOk(r)

    def test_jpost(self):
        with HTTMock(post):
            r = self.mixin.jpost("http://localhost:5001/test", data=DATA)
            self.assertOk(r)

    def test_jput(self):
        with HTTMock(put):
            r = self.mixin.jput("http://localhost:5001/test", data=DATA)
            self.assertOk(r)

    def test_jpatch(self):
        with HTTMock(patch):
            r = self.mixin.jpatch("http://localhost:5001/test", data=DATA)
            self.assertOk(r)

    def test_jdelete(self):
        with HTTMock(delete):
            r = self.mixin.jdelete("http://localhost:5001/test", data=DATA)
            self.assertOk(r)

    def raises_on_500_status_code(self):
        with HTTMock(return_500):
            self.assertRaises(InternalServerError, self.mixin.jget("localhost"))
            self.assertRaises(InternalServerError, self.mixin.jpost("localhost"))
            self.assertRaises(InternalServerError, self.mixin.jput("localhost"))
            self.assertRaises(InternalServerError, self.mixin.jpatch("localhost"))
            self.assertRaises(InternalServerError, self.mixin.jdelete("localhost"))