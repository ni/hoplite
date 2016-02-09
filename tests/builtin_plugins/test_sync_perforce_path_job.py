import os
import platform
import shutil
import stat
import unittest2

from hoplite.builtin_plugins.constants import SyncPerforcePathJobConstants as KEYS
from hoplite.builtin_plugins.sync_perforce_path_job import run as sync_perforce_path
from hoplite.client.status_updater import MockStatusUpdater


class TestSyncPerforcePathJob(unittest2.TestCase):
    def setUp(self):
        self.opsys = platform.system().lower()
        if self.opsys == 'windows':
            self.workspace = "riormt_hoplite_test_windows"
            self.workspace_root = r"C:\riormt_hoplite_test_windows"
            self.export_location_path = "C:\\riormt_hoplite_test_windows\\microDAQ\\exportLocation"
        elif self.opsys == 'linux' or self.opsys == 'darwin':
            self.workspace = "riormt_hoplite_test_posix"
            self.workspace_root = "/tmp/riormt_hoplite_test_posix"
            self.export_location_path = "/tmp/riormt_hoplite_test_posix/microDAQ/exportLocation"
        self.status = MockStatusUpdater()

    def test_sync_works(self):
        try:
            synced_file = os.path.join(self.workspace_root, "microDAQ", "exportLocation")
            config = {
                KEYS.USER: "riormt",
                KEYS.P4_PORT: "penguin.natinst.com:1666",
                KEYS.PERFORCE_PATH: "//microDAQ/exportLocation",
                KEYS.CLIENT_WORKSPACE: self.workspace,
                KEYS.FORCE: True
            }
            sync_perforce_path(config, self.status)
            self.assertEqual(self.export_location_path, self.status.status["local_path"])
            self.assertTrue(os.path.exists(synced_file))
            self.assertTrue(self.status.status["succeeded"])
        finally:
            try:
                os.chmod(self.export_location_path, stat.S_IWRITE)
                shutil.rmtree(self.workspace_root)
            except OSError:
                self.fail("Directory was not synced from perforce...")

    def test_sync_errors(self):
        config = {
            KEYS.USER: "riormt",
            KEYS.P4_PORT: "penguin.natinst.com:1666",
            KEYS.PERFORCE_PATH: "//microDAQ",
            KEYS.CLIENT_WORKSPACE: self.workspace,
            KEYS.FORCE: True
        }
        sync_perforce_path(config, self.status)
        self.assertFalse(self.status.status["succeeded"])