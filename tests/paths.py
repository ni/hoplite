import os

TESTS_PATH = os.path.split(__file__)[0]
TEST_RESOURCES_PATH = os.path.join(TESTS_PATH, "test_resources")
FTP_TEST_DIR_PATH = os.path.join(TEST_RESOURCES_PATH, "ftp_test")
TEST_PACKAGE_PATH = os.path.join(TEST_RESOURCES_PATH, "test_jobs_package")
TEST_ENTRY_POINT_PATH = os.path.join(TEST_RESOURCES_PATH, "test_entry_point")