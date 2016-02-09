"""
Installs a python package to the local python environment (directory containing
a setup.py)

Site-packages is reloaded after the install, so the package will be available
to import and the entry points will be registered correctly.

Example config::

    {
        KEYS.LOCAL_PATH: "C:\\path\\to\\package\\folder"
    }

Example return status::

    No Error:
    {
        "succeeded": True,
        "stdout": "All the stdout output"
    }

    Error (pip install failed):

    {
        "succeeded": False,
        "stdout": "All stdout",
        "errors": ["Error string"]
    }
"""
from hoplite.builtin_plugins.constants import (
    InstallPythonPackageJobConstants as KEYS)
from hoplite.client.remote_job_manager import RemoteJobManager
import pip
from cStringIO import StringIO
import sys


def install_package_with_pip(pip_cmd):
    out = None
    if pip_cmd is not None:
        backup = sys.stdout
        string_io = StringIO()
        sys.stdout = string_io
        pip_cmd = pip_cmd.split()
        if 'install' not in pip_cmd:
            pip_cmd.insert(0, 'install')
        ret = pip.main(pip_cmd)
        sys.stdout = backup
        out = string_io.getvalue()
        # FIXME: We should be calling string_io.close() but pip errors when we
        # do that
    return ret, out


def uninstall_package_with_pip(package_name):
    pip.main(['uninstall', package_name, '-y'])


def run(config, status):
    manager = RemoteJobManager("localhost", 5000)
    pip_cmd = config.get(KEYS.PIP_CMD, None) if config.get(KEYS.PIP_CMD, None) is not None else config.get(KEYS.LOCAL_PATH, None)

    if pip_cmd is None:
        status.update(
            {"succeeded": False, "errors": ["No local path specified"]})
        return
    ret, stdout = install_package_with_pip(pip_cmd)
    if ret:
        status.update(
            {"succeeded": False, "stdout": stdout, "errors": ["Pip returned a non-zero error code"]})
        return
    manager.reload_site_packages()
    status.update({"succeeded": True, "stdout": stdout})
