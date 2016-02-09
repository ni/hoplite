from setuptools import setup, find_packages
from test_jobs_package import constants as c

setup(
    name = "test-jobs",
    version = "0.1",
    packages = find_packages(),
    entry_points={
        'hoplite.test_jobs': [
            '{0}={1}'.format(c.WAIT_10_SECONDS_JOB_NAME, c.WAIT_10_SECONDS_JOB_MODULE),
            '{0}={1}'.format(c.CREATE_FILE_JOB_NAME, c.CREATE_FILE_JOB_MODULE),
            '{0}={1}'.format(c.THROW_AN_EXCEPTION_JOB_NAME, c.THROW_AN_EXCEPTION_JOB_MODULE),
            '{0}={1}'.format(c.JOB_FAILED_EXCEPTION_JOB_NAME, c.JOB_FAILED_EXCEPTION_JOB_MODULE)
        ]
    }
)
