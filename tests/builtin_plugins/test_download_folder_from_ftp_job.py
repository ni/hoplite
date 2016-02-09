import unittest2
import os
import socket
import tempfile
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from hoplite.builtin_plugins.download_folder_from_ftp_job import run
from hoplite.builtin_plugins.constants import DownloadFolderFromFtpJobConstants as FtpKeys
from hoplite.client.status_updater import MockStatusUpdater
import threading
import shutil
import platform

# Attempt to use IP rather than hostname (test suite will run a lot faster)
try:
    HOST = socket.gethostbyname('localhost')
except socket.error:
    HOST = 'localhost'

PORT = 8976


class FTPd(threading.Thread):
    """
    A threaded FTP server used for running tests.

    This is taken from the pyftpdlib tests because we need to be able to
    run our tests on all platforms, just like they do.

    This is basically a modified version of the FTPServer class which
    wraps the polling loop into a thread. This allows tests to run
    with a FTP Server that we create and start for each test.

    The instance returned can be used to start(), stop() and
    eventually re-start() the server.
    """
    handler = FTPHandler
    server_class = FTPServer

    def __init__(self, addr=None):
        threading.Thread.__init__(self)
        self.__serving = False
        self.__stopped = False
        self.__lock = threading.Lock()
        self.__flag = threading.Event()
        if addr is None:
            addr = (HOST, PORT)

        authorizer = DummyAuthorizer()
        test_dir = os.path.split(os.path.split(__file__)[0])[0]
        ftp_dir = os.path.join(test_dir, "test_resources", "ftp_test")
        authorizer.add_anonymous(ftp_dir)
        authorizer.add_user("no_pass", "", ftp_dir)
        authorizer.add_user("with_pass", "password", ftp_dir)
        self.handler.authorizer = authorizer
        # lowering buffer sizes = more cycles to transfer data
        # = less false positive test failures
        self.handler.dtp_handler.ac_in_buffer_size = 32768
        self.handler.dtp_handler.ac_out_buffer_size = 32768
        self.server = self.server_class(addr, self.handler)
        self.host, self.port = self.server.socket.getsockname()[:2]

    def __repr__(self):
        status = [self.__class__.__module__ + "." + self.__class__.__name__]
        if self.__serving:
            status.append('active')
        else:
            status.append('inactive')
        status.append('%s:%s' % self.server.socket.getsockname()[:2])
        return '<%s at %#x>' % (' '.join(status), id(self))

    @property
    def running(self):
        return self.__serving

    def start(self, timeout=0.001):
        """Start serving until an explicit stop() request.
        Polls for shutdown every 'timeout' seconds.
        """
        if self.__serving:
            raise RuntimeError("Server already started")
        if self.__stopped:
            # ensure the server can be started again
            FTPd.__init__(self, self.server.socket.getsockname(), self.handler)
        self.__timeout = timeout
        threading.Thread.start(self)
        self.__flag.wait()

    def run(self):
        self.__serving = True
        self.__flag.set()
        while self.__serving:
            self.__lock.acquire()
            self.server.serve_forever(timeout=self.__timeout, blocking=False)
            self.__lock.release()
        self.server.close_all()

    def stop(self):
        """Stop serving (also disconnecting all currently connected
        clients) by telling the serve_forever() loop to stop and
        waits until it does.
        """
        if not self.__serving:
            raise RuntimeError("Server not started yet")
        self.__serving = False
        self.__stopped = True
        self.join()


class TestDownloadFolderFromFTPJob(unittest2.TestCase):
    server_class = FTPd

    def setUp(self):
        self.server = self.server_class()
        self.server.start()

        test_dir = os.path.split(os.path.split(__file__)[0])[0]
        self.temp_dir = tempfile.mkdtemp(dir=os.path.join(test_dir, "test_resources"))
        self.config = {
            FtpKeys.SERVER_ADDRESS: HOST,
            FtpKeys.SERVER_PORT: PORT,
            FtpKeys.FTP_ROOT: "/",
            FtpKeys.DEST_ROOT: self.temp_dir
        }

    def tearDown(self):
        self.server.stop()
        self.server.join()
        shutil.rmtree(self.temp_dir)

    def test_copies_folder_anonymous(self):
        self._run_job(self.config)
        self._validate_directory(self.temp_dir)

    def test_copies_folder_user_no_pass(self):
        self.config[FtpKeys.USERNAME] = "no_pass"
        self._run_job(self.config)
        self._validate_directory(self.temp_dir)

    def test_copies_folder_user_pass(self):
        self.config[FtpKeys.USERNAME] = "with_pass"
        self.config[FtpKeys.PASSWORD] = "password"
        self._run_job(self.config)
        self._validate_directory(self.temp_dir)

    def test_errors_if_remote_dir_doesnt_exist(self):
        self.config[FtpKeys.FTP_ROOT] = "/not/exist"
        status = self._run_job(self.config)
        self.assertEqual(status.status, {"error": "Could not open the ftp directory: '/not/exist'"})

    def test_errors_if_local_dir_doesnt_exist(self):
        self.config[FtpKeys.DEST_ROOT] = "/fake/path"
        status = self._run_job(self.config)
        self.assertEqual(status.status, {"error": "Local path does not exist: '/fake/path'"})

    def test_remote_server_does_not_exist(self):
        self.config[FtpKeys.SERVER_ADDRESS] = "not-real-address"
        status = self._run_job(self.config)

        opsys = platform.system().lower()
        if opsys == 'windows':
            self.assertEqual(status.status, {"error": "[Errno 11004] getaddrinfo failed"})
        elif opsys == 'linux':
            self.assertEqual(status.status, {'error': '[Errno -2] Name or service not known'})
        elif opsys == 'darwin':
            self.assertEqual(status.status, {'error': '[Errno 8] nodename nor servname provided, or not known'})

    def test_file_already_exists_on_local_overwrites(self):
        # stat()[-2] is the time of mose recent content modification
        self._run_job(self.config)
        first_mod_date = os.stat(os.path.join(self.temp_dir, "test_file_1.txt"))[-2]
        self._run_job(self.config)
        second_mod_date = os.stat(os.path.join(self.temp_dir, "test_file_1.txt"))[-2]
        self.assertGreaterEqual(second_mod_date, first_mod_date)

    def _validate_directory(self, directory):
        file_1_path = os.path.join(directory, "test_file_1.txt")
        file_2_path = os.path.join(directory, "test_directory_1", "test_file_2.txt")

        with open(file_1_path) as f:
            expected = "Hello world!"
            actual = f.read()
            self.assertEqual(expected, actual)

        with open(file_2_path) as f:
            expected = "Hello moto!"
            actual = f.read()
            self.assertEqual(expected, actual)

    def _run_job(self, config):
        status = MockStatusUpdater()
        run(config, status)
        return status