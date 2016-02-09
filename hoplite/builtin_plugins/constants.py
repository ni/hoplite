
DOWNLOAD_NETWORK_FOLDER_JOB_NAME = "hoplite.plugins.download_network_folder_job"
DOWNLOAD_FOLDER_FROM_FTP_JOB_NAME = "hoplite.plugins.download_folder_from_ftp_job"
UPLOAD_TO_NETWORK_FOLDER_JOB_NAME = "hoplite.plugins.upload_to_network_folder_job"
INSTALL_PYTHON_PACKAGE_JOB_NAME = "hoplite.plugins.install_python_package_job"
SYNC_PERFORCE_PATH_JOB_NAME = "hoplite.plugins.sync_perforce_path_job"


class DownloadFolderFromFtpJobConstants(object):
    DEST_ROOT = "dest_root"
    FTP_ROOT = "ftp_root"
    SERVER_ADDRESS = "server_address"
    SERVER_PORT = "server_port"
    USERNAME = "username"
    PASSWORD = "password"


class InstallPythonPackageJobConstants(object):
    LOCAL_PATH = "LOCAL_PATH"
    PIP_CMD = "PIP_CMD"


class SyncPerforcePathJobConstants(object):
    USER = "USER"
    CLIENT_WORKSPACE = "CLIENT_WORKSPACE"
    P4_HOST = "P4_HOST"
    P4_PORT = "P4_PORT"
    PERFORCE_PATH = "PERFORCE_PATH"
    FORCE = "FORCE"
