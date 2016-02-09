import shutil
import os
import platform
from subprocess import Popen, PIPE, STDOUT


def authenticate_network_resource(resource, username, password):
    """ Authenticate a network share on the local machine
    @param resource: The UNC path for the network share
    @param username: The username to use. Domain names should be prefixed like
        this r'AMER\nitest'
    @param password: The password for user
    @return: None
    """

    opsys = platform.system().lower()

    if opsys == 'windows':
        _authenticate_network_resource_windows(
            resource=resource, username=username, password=password)
    else:
        raise NotImplementedError(
            'Support for this method on %s is not yet implemented.' % opsys)


def _authenticate_network_resource_windows(resource, username, password):
    unc, path = os.path.splitunc(resource)
    if username is not None and password is not None:
        cmdList = ["NET", "USE", unc, "/USER:{0}".format(username), password]
    else:
        cmdList = ["NET", "USE", unc]

    proc = Popen(cmdList, stdout=PIPE, stderr=STDOUT, shell=True)
    rtn = proc.communicate()[0]
    if 0 != proc.returncode:
        error = RuntimeError(
            "Error %d from %s'\n%s" % (
                proc.returncode, " ".join(cmdList), rtn))
        error.returncode = proc.returncode
        raise error
    return rtn


def download_network_folder(network_path, local_path, user, password):
    """
    Downloads the directory at network_path into local_path
    The folder in local_path must not exist
    """
    authenticate_network_resource(network_path, user, password)
    shutil.copytree(network_path, local_path)


def upload_folder_to_network_directory(network_path, local_path, user, password):
    """
    Uploads the folder at local_path to the network_path
    The upload location in network_path must not exist
    """
    authenticate_network_resource(network_path, user, password)
    shutil.copytree(local_path, network_path)
