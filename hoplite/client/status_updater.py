"""
Role
====

:py:class:`hoplite.client.StatusUpdater` is one of the paramters of a job's
run() function.


:py:class:`hoplite.client.MockStatusUpdater` is for use during job development

Example
=======
While developing a job, you might want to invoke the job script from the
command line.  By using :py:class:`hoplite.client.MockStatusUpdater` you can
call the run method of your job and have all your status updates printed to the
console.

    ..  code-block:: python

        def run(config, status):
            # Some python code here
            pass

        if __name__ == "__main__":
            config = {}
            run(config, MockStatusUpdater())

API
===
"""
import requests
from hoplite.serializer import hoplite_dumps
from hoplite.exceptions import JobDoesNotExistError


class StatusUpdater(object):
    """
    Used to update the status of the job running on the daemon.
    This is passed in to the job's run() function when it is invoked.
    """
    def __init__(self, addr, uuid, api_key):
        self.addr = addr
        self._uuid = uuid
        self._daemon_addr = 'http://{0}'.format(self.addr)
        self._api_key = api_key
        self.status = {}

    def update(self, status):
        """
        Updates the job's status on the server that created it.

        :param dict status: The new status of the job
        """
        self.status = status
        body = hoplite_dumps({
            "api_key": self._api_key,
            "status": status
        })
        url = self._daemon_addr + '/jobs/{0}'.format(self._uuid)
        headers = {'content-type': 'application/json'}
        r = requests.put(url, data=body, headers=headers)
        if r.status_code == 404:
            raise JobDoesNotExistError


class MockStatusUpdater(object):
    """
    For use while developing a job
    """
    def __init__(self, addr="0.0.0.0:5000", uuid="{0}", api_key=""):
        self.addr = addr
        self._uuid = uuid
        self._daemon_addr = 'http://{0}'.format(self.addr)
        self._api_key = api_key
        self.status = {}

    def update(self, status):
        """
        Prints the status to stdout for debugging and sets the
        member variable status for use in testing status updates

        :param status: status dictionary
        """
        self.status = status
        print(self.status)
