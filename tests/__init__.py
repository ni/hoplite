from unittest2 import TestCase
from .utils import FlaskTestCaseMixin, StatusCodeTestMixin
from hoplite.builtin_plugins.install_python_package_job import install_package_with_pip, uninstall_package_with_pip
from hoplite.api.root import reload_site_packages
from tests.paths import TEST_PACKAGE_PATH


class HopliteTestCase(TestCase):
    def setUp(self):
        """
        This imports the test_jobs_package, which is required by many tests
        to exercise different parts of hoplite

        __import__ returns a module object which can then be used to invoke
        the different sub-modules imported by name in the last argument. I am
        using this because we install the package at runtime with pip,
        so we have to import at runtime.

        This simplifies development where new test plugins need to be created
        to exercise code. It also allows us to have one dev_requirements file
        instead of one per OS.
        """
        # Monkey patch pip so it doesn't mess with logging. Otherwise, presence
        # of nose xunit logging handlers will
        # cause an error when pip tries to set logging things
        def blank_func(blank_arg):
            pass
        import pip.basecommand
        pip.basecommand.__dict__['logging_dictConfig'] = blank_func

        install_package_with_pip(TEST_PACKAGE_PATH)
        reload_site_packages()
        self.test_jobs_module = __import__('test_jobs_package', globals(), locals(), ['constants',
                                                                                      'throw_an_exception_job',
                                                                                      'wait_10_seconds_job',
                                                                                      'create_file_job',
                                                                                      'throw_job_failed_exception'], -1)

    def tearDown(self):
        uninstall_package_with_pip('test-jobs')
        reload_site_packages()


class HopliteAppTestCase(HopliteTestCase, FlaskTestCaseMixin, StatusCodeTestMixin):
    def _create_app(self):
        raise NotImplementedError

    def setUp(self):
        super(HopliteAppTestCase, self).setUp()
        self.app = self._create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        super(HopliteAppTestCase, self).tearDown()
        self.app_context.pop()
