import unittest2
import os
import tempfile
import shutil
import pip
from hoplite.client.status_updater import MockStatusUpdater
from hoplite.builtin_plugins.constants import InstallPythonPackageJobConstants as KEYS
from hoplite.builtin_plugins import install_python_package_job
from httmock import urlmatch, response, HTTMock

# Monkey patch pip so it doesn't mess with logging. Otherwise, presence of nose xunit logging handlers will cause an
# error when pip tries to set logging things
def blank_func(blank_arg):
    pass
import pip.basecommand
pip.basecommand.__dict__['logging_dictConfig'] = blank_func


@urlmatch(path='/reload$')
def reload_site_packages(url, request):
    return response(200)


class TestInstallPythonPackage(unittest2.TestCase):
    def test_install_from_local_path(self):
        setup_str = "from setuptools import setup, find_packages;setup(name='poopy', version='0.1', packages=find_packages())"
        tempdir = tempfile.mkdtemp()
        try:
            setup_py = open(os.path.join(tempdir, "setup.py"), 'w')
            setup_py.write(setup_str)
            setup_py.close()

            package_path = os.path.join(tempdir, "poopy")
            os.mkdir(package_path)

            init_file = open(os.path.join(package_path, "__init__.py"), 'w')
            init_file.close()

            config = {KEYS.LOCAL_PATH: tempdir}
            status = MockStatusUpdater()
            with HTTMock(reload_site_packages):
                install_python_package_job.run(config, status)
            self.assertTrue(status.status["succeeded"])
            try:
                import poopy
            except ImportError:
                self.fail("Could not import installed package")
        finally:
            pip.main(['uninstall', '-y', "poopy"])
            shutil.rmtree(tempdir)

    def test_install_fails_success_false_stdout_info(self):
        setup_str = "raise ValueError('I FAILED!')"
        tempdir = tempfile.mkdtemp()
        try:
            setup_py = open(os.path.join(tempdir, "setup.py"), 'w')
            setup_py.write(setup_str)
            setup_py.close()

            config = {KEYS.LOCAL_PATH: tempdir}
            status = MockStatusUpdater()


            install_python_package_job.run(config, status)

            self.assertFalse(status.status["succeeded"])

            # Because we monkey patch pip so it doesn't mess up nose xunit logging, the traceback info goes to the
            # console rather than to status.status.stdout
            #self.assertRegexpMatches(status.status["stdout"], "Traceback")

            self.assertIn("Pip returned a non-zero error code", status.status["errors"])
        finally:
            shutil.rmtree(tempdir)

    def test_missing_local_path_returns_errors(self):
        config = {}
        status = MockStatusUpdater()

        install_python_package_job.run(config, status)

        self.assertFalse(status.status["succeeded"])
        self.assertIn("No local path specified", status.status["errors"])