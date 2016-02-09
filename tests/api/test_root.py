from hoplite.utils import server_logging
import os
import sys
import platform
from tests.api import HopliteApiTestCase
import tempfile
import shutil
import pip
import pkg_resources


logger = server_logging.get_server_logger(__name__)

class RootSiteTestCase(HopliteApiTestCase):
    def setUp(self):
        super(RootSiteTestCase, self).setUp()

    '''
    This test is failing intermittently. I think it has to do with how exactly things are installed into the
    virtual environment and when/how the packages are reloaded.

    def test_reload_site_packages(self):
        opsys = platform.system().lower()
        python_exe_path = sys.executable
        bin_path = os.path.split(python_exe_path)[0]
        venv_path = bin_path
        site_path = ""
        if opsys == 'windows':
            if hasattr(sys, 'real_prefix'):  # If running in virtual environment, we must account for different folder structure
                site_path = os.path.join(venv_path, "..", "Lib", "site-packages")
            else:
                site_path = os.path.join(venv_path, "Lib", "site-packages")
        elif opsys == 'linux' or opsys == 'darwin':
            if hasattr(sys, 'real_prefix'):  # If running in virtual environment, we must account for different folder structure
                site_path = os.path.join(venv_path, "..", "lib", "python{0}.{1}".format(sys.version_info[0], sys.version_info[1]),
                                        "site-packages")
            else:
                site_path = os.path.join(venv_path, "lib", "python{0}.{1}".format(sys.version_info[0], sys.version_info[1]),
                                        "site-packages")

        pth_file_path = os.path.join(site_path, "test.pth")
        try:
            pth_file = open(pth_file_path, 'w+')
            pth_file.write(os.path.abspath("./tests"))
            pth_file.close()
            r = self.client.put('/reload')
            self.assertOk(r)
        except Exception, e:
            os.remove(pth_file_path)
            raise e
        # This will raise if the path is not in sys.path
        sys.path.remove(os.path.abspath("./tests"))
    '''

    def test_loads_new_entry_points(self):
        setup_str = "from setuptools import setup, find_packages;setup(name='TestEntryPointPackage', version='0.1', packages=find_packages(), entry_points={'test.entry': ['job1=tepp.myjob']})"

        tempdir = tempfile.mkdtemp()
        try:
            setup_py = open(os.path.join(tempdir, "setup.py"), 'w')
            setup_py.write(setup_str)
            setup_py.close()
            package_path = os.path.join(tempdir, "tepp")
            os.mkdir(package_path)
            init_file = open(os.path.join(package_path, "__init__.py"), 'w')
            init_file.close()
            myjob = open(os.path.join(package_path, "myjob.py"), 'w')
            myjob.close()

            pip.main(['install', tempdir])
            r = self.client.put('/reload')
            self.assertOk(r)

            count = 0
            for entry_point in pkg_resources.iter_entry_points(group="test.entry"):
                self.assertEqual(entry_point.name, "job1")
                count += 1
                if count > 1:
                    self.fail("test.entry entry point has more than one definition")
        finally:
            pip.main(['uninstall', '-y', "TestEntryPointPackage"])
            shutil.rmtree(tempdir)


