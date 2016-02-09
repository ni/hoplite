"""
Role
====
Used to manage jobs on a remote hoplite server. This can be used to issue
commands to the job or get info about the job.
This is a wrapper around most of the commands in :ref:`REST-API-Jobs`

API
===
"""
import pickle
import time

from hoplite.client.helpers import ClientMixin
from hoplite.exceptions import (
    JobDoesNotExistError,
    TimeoutError,
    ConnectionError,
    JobFailedError)
from hoplite.serializer import hoplite_loads
import requests.exceptions


class RemoteJob(ClientMixin):
    """
    The representation of a job on a remote hoplite server
    """

    def __init__(self, address, port=5000, name="", uuid="", api_key="", config={}):
        """
        :param address: IP address or hostname of the computer running the job.
            If desired, the address may be in the form "address:port", rather
            than specifying the port in the second parameter
        :param port: Port of the remote computer hoplite is listening on. This
            is ignored if the address includes the port
        :param name: qualified name of the job to run
        :param uuid: the uuid of the job. If left blank then job will be
            created by the daemon running on addr
        :type uuid: string or None
        :param api_key: this is used to only allow the running job to update
            its own status
        :raises: InvalidAddressError
        :raises: JobDoesNotExistError
        :raises: ConnectionError
        """
        if ':' in address:
            self.address = address.split(':')[0]
            self.port = address.split(':')[1]
        else:
            self.address = address
            self.port = port
        self._daemon_addr = 'http://{0}:{1}'.format(self.address, self.port)
        self._config = config
        self.name = name
        self.uuid = uuid
        self._api_key = api_key
        self._last_poll = 0

        try:
            if not self.uuid:
                self._create_job()
            self._get_job()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(self.address)

    def config(self, force=False):
        """
        Get the config dictionary for this job

        :return: the configuration dictionary the job was created with
        :rtype: dict
        """
        self._get_job(force)
        return self._config

    def status(self, force=False):
        """
        Get the status dictionary of the job

        :return: the status dictionary of the job
        :rtype: dict
        :raises JobFailedError: if the job raised an exception
        """
        self._get_job(force)
        exception_dict = self._status.get("exception", None)
        if exception_dict:
            # Raise an exception, being sure to store the information from the
            # previous exception. This is so that stack traces for every job
            # are preserved, in the event that jobs call other jobs which then
            # throw exceptions.
            raise JobFailedError(
                self.address,
                self.uuid,
                pickle.loads(exception_dict['traceback']),
                exception_dict['previous_exception'])
        return self._status

    def start(self):
        """
        Start the job

        :return: true if the job was started successfully
        :raises JobDoesNotExistError: Job does not exist on the server
        """
        self._get_job()
        resp = self.jput(
            self._daemon_addr + '/jobs/{0}/start'.format(self.uuid))
        return resp.json()["started"]

    def join(self, timeout=-1):
        """
        This will block until the job is finished and then return True.
        Timeout is in seconds.

        Blocks infinitely by default (timeout=-1).

        :raises TimeoutError: The specified timeout was reached
        :raises JobFailedError: The job threw an exception
        """
        num_seconds = 0
        poll_interval = .05
        while num_seconds < timeout or timeout == -1:
            if self.finished():
                return True
            time.sleep(poll_interval)
            num_seconds += poll_interval
        raise TimeoutError(self.uuid)

    def kill(self, force=False):
        """
        Kill the job

        :return: true if the kill command was sent successfully. Success here
            does not mean the job is stopped, it only means that a kill signal
            was successfully sent to the job
        :rtype: bool
        :raises JobDoesNotExistError: if the job does not exist on the targeted
            server
        """
        self._get_job(force)
        resp = self.jput(
            self._daemon_addr + '/jobs/{0}/kill'.format(self.uuid))
        return hoplite_loads(str(resp.text))["killed"]

    def running(self, force=False):
        """
        :return: true if the job is currently executing on the target machine
        :rtype: bool
        :raises JobDoesNotExistError: Job not found on the server
        """
        self._get_job(force)
        return self._running

    def finished(self, force=False):
        """
        Returns true if the job on the target machine is no longer executing

        :return: If the job has run and is currently not running
        :rtype: bool
        :raises JobDoesNotExistError: Job not found on the server
        :raises JobFailedError: Job raised an exception
        """
        self.status(force)
        return self._finished

    def _get_job(self, force=False):
        """

        I call this before most other requests to get the status code sanity
        check.
        This method is rate limited for sanity
        """
        time_elapsed = time.time() - self._last_poll
        if time_elapsed > .2 or force:
            resp = self.jget(self._daemon_addr + '/jobs/{0}'.format(self.uuid))
            if resp.status_code == 404:
                raise JobDoesNotExistError
            self._set_attributes_from_response_json(
                hoplite_loads(str(resp.text)))
            self._last_poll = time.time()

    def _create_job(self):
        job_data = {"name": self.name, "config": self._config, "port": self.port}
        resp = self.jpost(self._daemon_addr + '/jobs', data=job_data)
        if resp.status_code == 400:
            raise JobDoesNotExistError(hoplite_loads(str(resp.text))["error"])
        self._set_attributes_from_response_json(hoplite_loads(str(resp.text)))

    def _set_attributes_from_response_json(self, resp_dict):
        job = resp_dict
        self.uuid = job["uuid"]
        self.name = job["name"]
        self._status = job.get("status", {})
        self._config = job.get("config", {})
        self._running = job.get("running", False)
        self._finished = job.get("finished", False)
