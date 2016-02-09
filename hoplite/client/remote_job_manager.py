"""
Role
====
Used to communicate with a remote hoplite server. This can be used to create
jobs and to manage the job plugin search paths. This is a wrapper over the
:ref:`REST-API-Server` and :ref:`REST-API-Job-Plugins`.

API
===
"""
import logging
import socket
import time
from hoplite.client.helpers import ClientMixin
from hoplite.client.remote_job import RemoteJob
from hoplite.serializer import hoplite_loads
from hoplite.exceptions import TimeoutError

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class RemoteJobManager(ClientMixin):
    """
    Used to communicate with a remote hoplite server
    """
    def __init__(self, address, port=5000):
        """
        :param address: IP address or hostname of the remote computer. If
            desired, the address may be in the form "address:port", rather than
            specifying the port in the second parameter
        :param port: The port the hoplite server is listening on. This is
            ignored if the address includes the port
        """
        if ':' in address:
            self.address = address.split(':')[0]
            self.port = address.split(':')[1]
        else:
            self.address = address
            self.port = port
        self._daemon_addr = 'http://{0}:{1}'.format(self.address, self.port)

    def is_available(self):
        """
        Find if the hoplite process is accessible on the remote target

        :return: True if hoplite is available and listening on the target
        :rtype: Boolean
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.address, self.port))
            s.close()
        except socket.error:
            return False
        return True

    def wait_for_available(self, retry_period_s=2, retries=150):
        """
        Waits for Hoplite to be active. If it finds hoplite is active before
        the timeout.

        :param int retry_period_s: The number of seconds between retying to
            connect to Hoplite
        :param int retries: The number of attempts to connect to Hoplite to
            make before throwing an exception
        """
        estimated_units = "seconds"
        estimated_timeout = retry_period_s * retries
        if estimated_timeout >= 60:
            estimated_timeout = estimated_timeout/60
            estimated_units = "minutes"

        while True:
            if self.is_available():
                break
            time.sleep(retry_period_s)
            retries -= 1
            if retries <= 0:
                errmsg = 'Hoplite Server could not be reached on host "{0}"'\
                         ' after waiting for at least {1} {2}'.format(
                                self._daemon_addr,
                                estimated_timeout,
                                estimated_units)
                logger.error(errmsg)
                raise TimeoutError(errmsg)

    def get_job(self, uuid):
        """
        Get the job identified by the uuid

        :param str uuid: UUID of the job to get
        :return: the job that matches the uuid
        :rtype: :py:class:`hoplite.client.RemoteJob`
        """
        return RemoteJob(self.address, self.port, uuid=uuid)

    def create_job(self, plugin_name, config):
        """
        Create a job

        :param str plugin_name: name of the plugin you want to run in the job
        :param dict config: the configuration dictionary for the job
        :return: a RemoteJob to access the created job with
        :rtype: :py:class:`hoplite.client.RemoteJob`
        """
        return RemoteJob(
            self.address, self.port, name=plugin_name, config=config)

    def get_running_jobs(self):
        """
        Get a list of jobs that are currently running
        """
        remote = self._daemon_addr + '/jobs/running'
        r = self.jget(remote)
        return hoplite_loads(str(r.text))["jobs"]

    def get_job_plugins(self):
        """
        Get the list of job builtin_plugins that have been loaded

        :return: list of available job_plugins
        :rtype: list of strings
        """
        remote = self._daemon_addr + '/job_plugins'
        r = self.jget(remote)
        return hoplite_loads(str(r.text))["job_plugins"]

    def reload_site_packages(self):
        """
        Force a reload of the local site-packages directory
        that the server uses to look for installed packages

        This allows you to have hoplite load entry points from
        newly installed packages without restarting the hoplite
        instance
        """
        remote = self._daemon_addr + '/reload'
        _ = self.jput(remote)
        return True
