import unittest2
import pip
import types
import os
import sys
from tests.paths import TEST_ENTRY_POINT_PATH
from hoplite.api.root import reload_site_packages
from hoplite.plugin_manager import EntryPointManager
import pkg_resources


def run_pip(pip_args):
    try:
        pip.main(initial_args=pip_args)
    except TypeError:  # The virtualenv pip uses "args" for the keyword argument name, rather than "initial_args"
        pip.main(args=pip_args)


class TestEntryPointManager(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        # Install hoplite so that its entry points are added
        pip_args = ["install", os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')]
        run_pip(pip_args)
        reload_site_packages()

    @classmethod
    def tearDownClass(cls):
        pip_args = ["uninstall", "hoplite", "-y"]
        run_pip(pip_args)

    def setUp(self):
        self.manager = EntryPointManager()

    def test_get_names_with_default_group_name(self):
        names = self.manager.get_plugin_names()
        self.assertIn('hoplite.plugins.download_folder_from_ftp_job', names)
        self.assertIn('hoplite.plugins.download_network_folder_job', names)
        self.assertIn('hoplite.plugins.upload_to_network_folder_job', names)

    def test_get_names_of_hot_installed_package(self):
        pip_args = ["install", TEST_ENTRY_POINT_PATH]
        run_pip(pip_args)
        reload_site_packages()
        for syspath in sys.path:
            pkg_resources.working_set.add_entry(syspath)
        try:
            self.manager = EntryPointManager('entry.point.test')
            names = self.manager.get_plugin_names()
            self.assertIn("entry_point_1", names)
            self.assertIn("entry_point_2", names)
        except Exception, e:
            raise e
        finally:
            pip_args = ["uninstall", "entrypointtest", "-y"]
            run_pip(pip_args)

    def test_get_module_returns_module(self):
        for entry_point in pkg_resources.iter_entry_points(group='hoplite.jobs'):
            if entry_point.name == 'hoplite.plugins.download_folder_from_ftp_job':
                mod = entry_point.load()
        self.assertIsInstance(mod, types.ModuleType)