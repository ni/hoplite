"""
@author Matt Murphy
"""
from hoplite.utils import server_logging
from job import Job
from hoplite.exceptions import JobDoesNotExistError, JobPluginDoesNotExistError
import uuid

logger = server_logging.get_server_logger(__name__)


class JobManager(object):
    """
    Class used by the server to manage jobs
    """

    def __init__(self, plugin_manager):
        """
        Initialize with unique id for this instance
        and the configured plugin paths
        """
        self.plugin_manager = plugin_manager
        self.jobs = {}

    def available_job_plugins(self):
        """
        Returns a list of jobs that can be created
        """
        return self.plugin_manager.get_plugin_names()

    def all_jobs(self):
        """
        Get all jobs that have been created
        """
        return self.jobs.values()

    def get_job(self, job_uuid):
        job = self.jobs.get(job_uuid, None)
        if job is None:
            raise JobDoesNotExistError(
                "Job with UUID: {0} does not exist".format(job_uuid))
        return job

    def create_job(self, name, config, running=False, port=5000):
        """
        Stores information about job in the job dictionary.
        If running is true then starts the job.
        """
        module = self._get_plugin_with_name(name)
        job_uuid = str(uuid.uuid4())
        job_api_key = str(uuid.uuid4())
        # TODO: Try/Catch if run does not exist
        job = Job(
            job_uuid,
            name,
            config,
            job_api_key,
            entry_point_group_name=self.plugin_manager.entry_point_group_name,
            port=port)
        logger.debug("Creating Job:{0} UUID:{1}".format(name, job_uuid))
        self.jobs[job.uuid] = job
        if running:
            job.start()
        return job

    def _get_plugin_with_name(self, name):
        plugin = self.plugin_manager.get_plugin_module_by_name(name)
        if plugin is None:
            raise JobPluginDoesNotExistError(name)
        return plugin

    def _clear(self):
        logger.warning("Clearing all jobs")
        self.jobs = {}
