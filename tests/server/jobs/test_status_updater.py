import json

from httmock import urlmatch, HTTMock, response
from hoplite.client.status_updater import StatusUpdater
from hoplite.exceptions import JobDoesNotExistError
import unittest2


@urlmatch(path='\/jobs\/someuuid$')
def update_status(url, request):
    if json.loads(request.body)["api_key"] == "apikeyhere":
        return response(200)
    return response(404)

class TestStatusUpdater(unittest2.TestCase):
    def test_update(self):
        with HTTMock(update_status):
            status = StatusUpdater('localhost:5001', "someuuid", "apikeyhere")
            status.update({"some": "status"})

    def test_update_raises(self):
        with HTTMock(update_status):
            status = StatusUpdater('localhost:5001', "someuuid", "wrongapikey")
            self.assertRaises(JobDoesNotExistError, status.update, {"some": "status"})

