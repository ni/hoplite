import psutil
import subprocess
import sys
import time
import unittest2

from hoplite.public_api import wait_for_hoplite
import remotable_test_resources.remotable_class as remotable_class
import remotable_test_resources.remotable_module as remotable_module


def start_hoplite_server(port_num):
    proc = psutil.Popen(
        '{} -c "import hoplite.main; hoplite.main.server_main([\'--port={}\'])"'.format(sys.executable, port_num),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    wait_for_hoplite('localhost', port_num)
    return proc


def tear_down_hoplite(process):
    l = process.get_children()
    for child in l:
        child.terminate()
        child.wait()
    process.terminate()
    process.wait()
    time.sleep(.5)


class TestRemotableClassMultipleHopliteInstance(unittest2.TestCase):
    def setUp(self):
        """
        This function has to use subprocess instead of multiprocessing. Otherwise, tests fail
        with the error "daemonic processes are not allowed to have children". This way, hoplite is
        run in a separate process.
        :return:
        """
        self.proc1 = start_hoplite_server(5001)
        self.proc2 = start_hoplite_server(5002)
        self.proc3 = start_hoplite_server(5003)
        self.proc4 = start_hoplite_server(5004)
        self.class_instance = remotable_class.TestClass('this_is@a#string', 12349)

    def tearDown(self):
        tear_down_hoplite(self.proc1)
        tear_down_hoplite(self.proc2)
        tear_down_hoplite(self.proc3)
        tear_down_hoplite(self.proc4)

    def test_return_none(self):
        ret1 = self.class_instance.remote_return_none('localhost:5001')
        ret2 = self.class_instance.remote_return_none('localhost:5002')
        ret3 = self.class_instance.remote_return_none('localhost:5003')
        ret4 = self.class_instance.remote_return_none('localhost:5004')
        self.assertIsNone(ret1)
        self.assertIsNone(ret2)
        self.assertIsNone(ret3)
        self.assertIsNone(ret4)

    def test_do_math(self):
        ret1 = self.class_instance.remote_do_math('localhost:5001', 15, 20)
        ret2 = self.class_instance.remote_do_math('localhost:5002', 7, 5)
        ret3 = self.class_instance.remote_do_math('localhost:5003', 2, 3)
        ret4 = self.class_instance.remote_do_math('localhost:5004', 133, 289)
        self.assertEqual(ret1, 15 * 20)
        self.assertEqual(ret2, 7 * 5)
        self.assertEqual(ret3, 2 * 3)
        self.assertEqual(ret4, 133 * 289)

    def test_do_math_async(self):
        job1 = self.class_instance.remote_async_do_math('localhost:5001', 15, 20)
        job2 = self.class_instance.remote_async_do_math('localhost:5002', 7, 5)
        job3 = self.class_instance.remote_async_do_math('localhost:5003', 2, 3)
        job4 = self.class_instance.remote_async_do_math('localhost:5004', 133, 289)
        job1.start()
        job2.start()
        job3.start()
        job4.start()
        while not job1.finished() and not job2.finished() and not job3.finished() and not job4.finished():
            time.sleep(.25)
        ret1 = job1.join()
        ret2 = job2.join()
        ret3 = job3.join()
        ret4 = job4.join()
        self.assertEqual(ret1, 15 * 20)
        self.assertEqual(ret2, 7 * 5)
        self.assertEqual(ret3, 2 * 3)
        self.assertEqual(ret4, 133 * 289)


class TestRemotableModuleMultipleHopliteInstance(unittest2.TestCase):
    def setUp(self):
        """
        This function has to use subprocess instead of multiprocessing. Otherwise, tests fail
        with the error "daemonic processes are not allowed to have children". This way, hoplite is
        run in a separate process.
        :return:
        """
        self.proc1 = start_hoplite_server(5001)
        self.proc2 = start_hoplite_server(5002)
        self.proc3 = start_hoplite_server(5003)
        self.proc4 = start_hoplite_server(5004)

    def tearDown(self):
        tear_down_hoplite(self.proc1)
        tear_down_hoplite(self.proc2)
        tear_down_hoplite(self.proc3)
        tear_down_hoplite(self.proc4)

    def test_return_none(self):
        ret1 = remotable_module.remote_return_none('localhost:5001')
        ret2 = remotable_module.remote_return_none('localhost:5002')
        ret3 = remotable_module.remote_return_none('localhost:5003')
        ret4 = remotable_module.remote_return_none('localhost:5004')
        self.assertIsNone(ret1)
        self.assertIsNone(ret2)
        self.assertIsNone(ret3)
        self.assertIsNone(ret4)

    def test_do_math(self):
        ret1 = remotable_module.remote_do_math('localhost:5001', 15, 20)
        ret2 = remotable_module.remote_do_math('localhost:5002', 7, 5)
        ret3 = remotable_module.remote_do_math('localhost:5003', 2, 3)
        ret4 = remotable_module.remote_do_math('localhost:5004', 133, 289)
        self.assertEqual(ret1, 15 * 20)
        self.assertEqual(ret2, 7 * 5)
        self.assertEqual(ret3, 2 * 3)
        self.assertEqual(ret4, 133 * 289)

    def test_do_math_async(self):
        job1 = remotable_module.remote_async_do_math('localhost:5001', 15, 20)
        job2 = remotable_module.remote_async_do_math('localhost:5002', 7, 5)
        job3 = remotable_module.remote_async_do_math('localhost:5003', 2, 3)
        job4 = remotable_module.remote_async_do_math('localhost:5004', 133, 289)
        job1.start()
        job2.start()
        job3.start()
        job4.start()
        while not job1.finished() and not job2.finished() and not job3.finished() and not job4.finished():
            time.sleep(.25)
        ret1 = job1.join()
        ret2 = job2.join()
        ret3 = job3.join()
        ret4 = job4.join()
        self.assertEqual(ret1, 15 * 20)
        self.assertEqual(ret2, 7 * 5)
        self.assertEqual(ret3, 2 * 3)
        self.assertEqual(ret4, 133 * 289)


def tear_down_hoplite(process):
    l = process.get_children()
    for child in l:
        child.terminate()
        child.wait()
    process.terminate()
    process.wait()
