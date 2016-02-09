from hoplite.utils import server_logging
import ftplib
import os
import socket
from ftplib import FTP
from hoplite.client.status_updater import MockStatusUpdater
from hoplite.builtin_plugins.constants import DownloadFolderFromFtpJobConstants as KEYS

logger = server_logging.get_job_logger(__name__)


def _get_files_in_dir(ftp_session, source, dest, status):
    filelist = ftp_session.nlst()
    for path in filelist:
        local_path = os.path.join(dest, path)
        remote_path = source + path
        try:
            # See if it's a directory
            new_remote_path = source + path + "/"
            ftp_session.cwd(source + path + "/")
            # It is! So we should create the directory on dest
            try:
                os.mkdir(local_path)
            except OSError:
                logger.debug("Dir: {0} already exists".format(local_path))
            logger.debug("Get Folder: {0}".format(new_remote_path))
            _get_files_in_dir(ftp_session, new_remote_path, local_path, status)
        except ftplib.error_perm:
            logger.debug("Get file: {0}".format(path))
            with open(local_path, "wb") as file_handle:
                ftp_session.retrbinary(
                    "RETR " + remote_path, file_handle.write)


def download_files(ftp_session, source, dest, status):
    # dest must already exist
    try:
        ftp_session.cwd(source)
    except ftplib.error_perm:
        # invalid entry (ensure input form: "/dir/folder/something/")
        msg = "Could not open the ftp directory: '{0}'".format(source)
        logger.error(msg)
        status.update({"error": msg})
        return
    if not os.path.isdir(dest):
        msg = "Local path does not exist: '{0}'".format(dest)
        logger.error(msg)
        status.update({"error": msg})
        return
    _get_files_in_dir(ftp_session, source, dest, status)


def run(config, status):
    """
    Job to recursively download a directory from an FTP server
    This will overwrite any files that are in the dest_root directory
    """
    ftp_addr = config.get(KEYS.SERVER_ADDRESS, "localhost")
    ftp_port = config.get(KEYS.SERVER_PORT, 21)
    ftp_root = config.get(KEYS.FTP_ROOT, "/")
    dest_root = config.get(KEYS.DEST_ROOT, "C:\\temp\\")
    user = config.get(KEYS.USERNAME, "")
    password = config.get(KEYS.PASSWORD, "")

    try:
        ftp_session = FTP()
        ftp_session.connect(ftp_addr, ftp_port)
        ftp_session.login(user, password)
    except socket.gaierror, e:
        status.update({"error": str(e)})
        logger.error(e)
        return
    logger.debug("connected {0}")
    download_files(ftp_session, ftp_root, dest_root, status)
    ftp_session.close()

if __name__ == "__main__":
    config_dict = {
        "server": "localhost",
        "ftp_root": "/",
        "dest_root": "C:\\temp\\",
    }
    run(config_dict, MockStatusUpdater())
