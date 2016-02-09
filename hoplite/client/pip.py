from hoplite.client.remote_job_manager import RemoteJobManager
from hoplite.builtin_plugins import constants


class Error(Exception):
    pass


def remote_install(host, package, port=5000, options=''):
    '''
    Provides a convient interface to install a python package
    through the hoplite job mechanism.

    :param string host: The host machine to install pip package
    :param string package: The package to install
    :param int port: The hoplite port to use (5000 by default)
    :param string options: The pip options to use ('' by default)
    '''
    job_manager = RemoteJobManager(host, port)
    job = job_manager.create_job(
        plugin_name=constants.INSTALL_PYTHON_PACKAGE_JOB_NAME,
        config={
            'PIP_CMD': 'install {0} {1}'.format(options, package)
        })
    job.start()
    job.join()
    status = job.status()
    if not status['succeeded']:
        raise Error(status['stdout'])
