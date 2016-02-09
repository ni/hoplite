from hoplite.builtin_plugins.utils.network_file_operations import download_network_folder
from hoplite.client.status_updater import MockStatusUpdater
import shutil
import os


def run(config, status):
    """
    Copies a folder from a network location and places it on the local disk
    This job is for Windows only (you better remember to escape your
    backslashes)
    **If overwrite is False local_path must not exist**
    Expected Config:
    {
        "network_path": "\\\\share\\something\\something\\something",
        "local_path": "C:\\Documents\\doesnotexist",
        "user": "DOMAIN\username",
        "password": "password",
        "overwrite": False
    }
    """
    network_path = config.get("network_path", None)
    local_path = config.get("local_path", None)
    user = config.get("user", "")
    password = config.get("password", "")
    overwrite = config.get("overwrite", False)

    if network_path is None:
        status.update(
            {"success": False, "error": "network_path not defined in config"})
        return
    if local_path is None:
        status.update(
            {"success": False, "error": "local_path not defined in config"})
        return

    if os.path.isdir(local_path):
        if overwrite:
            try:
                shutil.rmtree(local_path)
            except OSError as e:
                status.update({"success": False, "error": e})
                return
        else:
            status.update(
                {
                    "success": False,
                    "error": "Directory already exists: {0}".format(
                        local_path)
                })
            return

    if network_path.find('\\\\', 0, 2) == 0:
        stdout = ""
        try:
            stdout = download_network_folder(
                network_path, local_path, user, password)
        except RuntimeError as e:
            status.update({"success": False, "error": e})
            return
        status.update({"success": True, "stdout": stdout})
        return
    status.update({"error": "Invalid network path"})
