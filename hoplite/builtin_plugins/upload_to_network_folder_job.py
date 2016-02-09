from hoplite.builtin_plugins.utils.network_file_operations import upload_folder_to_network_directory
from hoplite.client.status_updater import MockStatusUpdater


def run(config, status):
    """
    Uploads a folder from the local disk to a network location
    This job is for Windows only (you better remember to escape your
    backslashes)
    **dest_path must not exist**
    Expected Config:
    {
        network_path: "\\\\share\\something\\something\\something",
        local_path: "C:\\Documents\\doesnotexist",
        user: "DOMAIN\username",
        password: "password"
    }
    """
    network_path = config.get("network_path", None)
    local_path = config.get("local_path", None)
    user = config.get("user", "")
    password = config.get("password", "")

    if network_path is None:
        status.update({"error": "network_path not defined in config"})
        return
    if local_path is None:
        status.update({"error": "local_path not defined in config"})
        return

    if network_path.find('\\\\', 0, 2) == 0:
        stdout = ""
        try:
            stdout = upload_folder_to_network_directory(
                network_path, local_path, user, password)
        except RuntimeError, e:
            status.update({"error": e})
        status.update({"success": True, "stdout": stdout})
        return
    status.update({"error": "Invalid network path"})
