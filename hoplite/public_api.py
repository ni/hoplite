import socket
import time
from hoplite.exceptions import TimeoutError

from urlparse import urlparse

from io import BytesIO
import pip
import sys
from subprocess import Popen, PIPE

from hoplite.remote_enabler import remotify

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def is_hoplite_available(address, port=5000):
    """
    Find if the hoplite process is accessible on the remote target

    :return: True if hoplite is available and listening on the target
    :rtype: Boolean
    """
    if ':' in address:
        temp_address = address.split(':')[0]
        port = address.split(':')[1]
        address = temp_address

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((address, port))
        s.close()
    except socket.error:
        return False
    return True


def wait_for_hoplite(address, port=5000, retry_period_s=10, retries=30):
    """
    Waits for Hoplite to be active. If it finds hoplite is active before
    the timeout.

    :param int retry_period_s: The number of seconds between retying to connect
        to Hoplite
    :param int retries: The number of attempts to connect to Hoplite to make
        before throwing an exception
    """
    estimated_units = "seconds"
    estimated_timeout = retry_period_s * retries
    if estimated_timeout >= 60:
        estimated_timeout /= 60
        estimated_units = "minutes"

    if ':' in address:
        temp_address = address.split(':')[0]
        port = address.split(':')[1]
        address = temp_address

    logger.info("Waiting for hoplite to become available on {0}:{1}".format(address, port))

    while True:
        if is_hoplite_available(address, port):
            logger.info("Hoplite is online at {0}:{1}".format(address, port))
            break
        time.sleep(retry_period_s)
        retries -= 1
        if retries <= 0:
            errmsg = 'Hoplite Server could not be reached on host "{0}:{1}" after waiting for at least {2} {3}'.format(
                     address,
                     port,
                     estimated_timeout,
                     estimated_units)
            logger.error(errmsg)
            raise TimeoutError(errmsg)


@remotify(__name__)
def install_python_package(package, server=None, options=None):
    """
    Installs a python package via pip
    :param package: Name of python package
    :param server: Server for pip to retrieve from. If no server is specified,
        then the default server will be used based on the pip configuration
        file in the user folder. Note that any server specified will be assumed
        to be a trusted host
    :param options: A list of options to use when installing the package.
    :type options: list of [str]
    :return: The output from running pip
    """
    from pip.status_codes import SUCCESS, ERROR, UNKNOWN_ERROR, VIRTUALENV_NOT_FOUND, PREVIOUS_BUILD_DIR_ERROR
    pip_error_codes = {
        ERROR: 'ERROR',
        UNKNOWN_ERROR: 'UNKNOWN_ERROR',
        VIRTUALENV_NOT_FOUND: 'VIRTUALENV_NOT_FOUND',
        PREVIOUS_BUILD_DIR_ERROR: 'PREVIOUS_BUILD_DIR_ERROR'
    }

    args = ['install', package]

    if options is not None:
        args += options

    if server is not None:
        logger.info('Installing {} from server: {}'.format(package, server))
        trusted_host = urlparse(server)[1]
        if ':' in trusted_host:
            trusted_host = trusted_host.split(':')[0]
        args += ['-i', server, '--trusted-host', trusted_host]
    else:
        logger.info('Installing {} from default Pypi server'.format(package))

    stdout_backup = sys.stdout
    stderr_backup = sys.stderr
    with BytesIO() as bytes_io:
        sys.stdout = bytes_io
        sys.stderr = bytes_io
        exit_code = pip.main(args)
        pip_output = bytes_io.getvalue()
    sys.stdout = stdout_backup
    sys.stderr = stderr_backup
    if exit_code == SUCCESS:
        return pip_output
    elif pip_error_codes.get(exit_code) is not None:
        # We could raise PipError, but it seems like it's intended only for
        # internal pip use.
        raise RuntimeError(
            'Pip exited with nonzero exit code: {} and output: {}'.format(
                pip_error_codes[exit_code], pip_output))
    else:
        raise RuntimeError(
            'Pip encountered an error while installing. Output: {}'.format(
                pip_output))


@remotify(__name__)
def uninstall_python_package(package):
    logger.info("Uninstalling %s with pip" % package)
    pip.main(['uninstall', package, '-y'])


@remotify(__name__)
def run_cmd_command(*args, **kwargs):
    """
    Runs a subprocess command.
    """
    if "stdout" in kwargs:
        kwargs.pop("stdout")
    p = Popen(*args, stdout=PIPE, stderr=PIPE, **kwargs)
    std_out, std_err = p.communicate()
    err_code = p.returncode
    return std_out, std_err, err_code
