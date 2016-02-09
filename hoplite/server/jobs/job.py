from multiprocessing import Process
from multiprocessing import Pipe

from hoplite.utils import server_logging
from hoplite.exceptions import (
    JobAlreadyStartedError,
    JobNotStartedError,
    NotAuthorizedError)
from job_wrapper import job_wrapper
from hoplite.client.status_updater import StatusUpdater
from hoplite.plugin_manager import EntryPointManager


class Job(object):
    """
    Represents a job that has been created on the server
    """
    def __init__(self, job_uuid, name, config, api_key, entry_point_group_name="hoplite.jobs", port=5000):
        """
        @param job_uuid unique identifier for this job
        @param name the name of the job, corresponds to the plugin name
        @param config dictionary object containing configuration for the
            specific job
        """
        self.port = port
        self.uuid = job_uuid
        self.name = name
        self.config = config
        self._api_key = api_key
        self._status = {}
        self._process = None
        self._started = False
        self._killed = False
        self._pipe_to_self = None
        self._pipe_to_process = None
        # TODO: We need this workaround because in tests I create jobs that
        # don't have a corresponding loaded entry point
        # At some point the tests should be refactored to use jobs that exist
        # and we can get rid of this code
        module = EntryPointManager().get_plugin_module_by_name(name)
        logger_name = module.__name__ if module is not None else name
        self._logger = server_logging.get_job_logger(
            logger_name, uuid=self.uuid)
        self._entry_point_group_name = entry_point_group_name

    def running(self):
        """
        The current state of the process executing the job
        :return: Boolean describing if job is running
        """
        if self._process:
            return self._process.is_alive()
        return False

    def killed(self):
        """
        Checked if job has been killed.
        :return: Boolean describing if job was killed.
        """
        return self._killed

    def start(self):
        """
        Start the job. If the job has already been started before, a
        JobAlreadyStartedError is raised.
        """
        if self._started:
            raise JobAlreadyStartedError(self.uuid)
        if self.name:
            # TODO Testing hole here...We don't make sure updater is good or
            # anything
            updater = StatusUpdater(
                'localhost:{}'.format(self.port), self.uuid, self._api_key)
            self._pipe_to_process, self._pipe_to_self = Pipe()
            self._logger.debug(
                "Starting Job {0} UUID:{1}".format(self.name, self.uuid))
            self._process = Process(
                target=job_wrapper,
                args=(
                    self._pipe_to_self,
                    self.name,
                    self.config,
                    updater,
                    self._entry_point_group_name,
                    self.uuid))
            self._process.start()
            self._started = True

    def finished(self):
        """
        Returns True once the job has finished running.
        Will raise a JobNotStartedError if :meth:`job.start` has not been
        called
        :return: Boolean describing if the process has started and is no longer
            running
        """
        if self._process is None:
            raise JobNotStartedError(self.uuid)
        return not self._process.is_alive() and self._started

    def status(self):
        """
        Update exception dictionary of status if there is something available
        from the process pipe. Returns the updated status afterwards.
        :return: status dictionary from the job processes
        """
        if self._pipe_to_process:
            if self._pipe_to_process.poll():
                exception_dictionary = self._pipe_to_process.recv()
                self._status["exception"] = exception_dictionary
                self._pipe_to_process = None
        return self._status

    def update_status(self, api_key, status_update):
        if api_key != self._api_key:
            raise NotAuthorizedError
        self._status = dict(self._status.items() + status_update.items())
        self._logger.debug(
            "Update Status:{0} UUID:{1} Status:{2}".format(
                self.name, self.uuid, self._status))

    def kill(self):
        """
        Kills the job if has been started. Raises a JobNotStartedError if it
        has not started yet. If the job has already finished, the job will
        still be flagged as killed, but it will not have any further
        consequences.
        """
        if self._process is None:
            raise JobNotStartedError(self.uuid)
        self._logger.debug(
            "Terminating Job:{0} UUID:{1}".format(self.name, self.uuid))
        self._process.terminate()
        self._pipe_to_process = None
        self._pipe_to_self = None
        self._killed = True

    def to_dict(self):
        """
        Returns a dictionary representation of the job.
        Used to serialize job data using JSON for sending over the network.
        """
        d = {}
        d["uuid"] = self.uuid
        d["name"] = self.name
        d["config"] = self.config
        d["status"] = self.status()
        d["running"] = self.running()
        d["killed"] = self.killed()
        try:
            d["finished"] = self.finished()
        except JobNotStartedError:
            d["finished"] = False
        return d
