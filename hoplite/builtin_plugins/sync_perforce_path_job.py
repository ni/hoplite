"""
Sync down a path from perforce.

Example config::

    {
        KEYS.USER: "username",
        KEYS.P4_PORT: "perforce:1666",
        KEYS.PERFORCE_PATH: "//depot/path",
        KEYS.CLIENT_WORKSPACE: "client_spec_name",
        KEYS.FORCE: True
    }

Example return status::

    No Error:
    {
        "succeeded": True,
        "local_path": "C:\\path",  # The local path the perforce path was synced to
        "stdout": "All the stdout output" # Everything from stdout
    }

    Error:

    {
        "succeeded": False,
        "stdout": "All stdout",
        "stderr": "All stderr"
    }

"""
from hoplite.builtin_plugins.constants import (
    SyncPerforcePathJobConstants as KEYS)
from subprocess import Popen
from hoplite.client.status_updater import MockStatusUpdater
import tempfile
import os
import re


def p4_where_command(client_workspace, p4_path, p4_port, user):
    stdout_file = tempfile.mktemp()
    stdout_file_handle = open(stdout_file, 'w')
    perforce_where_command = ['p4', '-u', user, '-c', client_workspace, '-p', p4_port, 'where', p4_path]
    p4_where = Popen(perforce_where_command, stdout=stdout_file_handle)
    p4_where.communicate()
    p4_where.poll()
    while p4_where.returncode is None:
        p4_where.poll()
    stdout_file_handle.close()
    with open(stdout_file, 'r') as stdout_file_handle:
        p4_where_info = stdout_file_handle.read()
    # TODO: This regex covers windows and unix paths, but is only tested with
    # Unix paths. It needs a Windows test.
    m = re.search(r'((\w:.*$)|\s(/[^/].+))', p4_where_info)
    local_path = m.group().strip()
    return local_path


def p4_sync_command(client_workspace, p4_path, p4_port, user, force=True):
    force_flag = "-f" if force else ""
    perforce_command = ['p4', '-u', user, '-c', client_workspace, '-p', p4_port, 'sync', force_flag, p4_path]
    stdout_file = tempfile.mktemp()
    stdout_file_handle = open(stdout_file, 'w')
    stderr_file = tempfile.mktemp()
    stderr_file_handle = open(stderr_file, 'w')
    p4_sync = Popen(
        perforce_command, stdout=stdout_file_handle, stderr=stderr_file_handle)
    p4_sync.communicate()
    p4_sync.poll()
    while p4_sync.returncode is None:
        p4_sync.poll()
    stdout_file_handle.close()
    stderr_file_handle.close()
    with open(stdout_file, 'r') as stdout_file_handle:
        stdout = stdout_file_handle.read()
    with open(stderr_file, 'r') as stderr_file_handle:
        stderr = stderr_file_handle.read()

    os.remove(stdout_file)
    os.remove(stderr_file)
    return stderr, stdout


def run(config, status):
    user = config.get(KEYS.USER, "")
    client_workspace = config.get(KEYS.CLIENT_WORKSPACE, "")
    p4_port = config.get(KEYS.P4_PORT, "perforce:1666")
    force = config.get(KEYS.FORCE, True)
    p4_path = config.get(KEYS.PERFORCE_PATH, "")

    stderr, stdout = p4_sync_command(
        client_workspace, p4_path, p4_port, user, force=force)

    if stderr == "":
        local_path = p4_where_command(client_workspace, p4_path, p4_port, user)
        if re.search('\.\.\.', local_path):
            # Perforce puts /... if you synced a directory, we need to remove
            # it to have a valid path
            local_path = os.path.dirname(local_path)
        status.update(
            {"succeeded": True, "stdout": stdout, "local_path": local_path})
    else:
        status.update({"succeeded": False, "stdout": stdout, "stderr": stderr})
