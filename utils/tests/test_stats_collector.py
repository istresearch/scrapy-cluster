'''
Offline utility tests
'''
import redis
from unittest import TestCase
from scutils.stats_collector import (AbstractCounter, ThreadedCounter)
from mock import MagicMock
from mock import patch


class TestStatsAbstract(TestCase):

    def test_default_key(self):
        ac = AbstractCounter()
        self.assertEqual('default_counter', ac.get_key())

    def test_overloaded_key(self):
        ac = AbstractCounter('aKey')
        self.assertEqual('aKey', ac.get_key())

    def test_not_implemented(self):
        ac = AbstractCounter()

        try:
            ac.increment()
            self.fail("increment should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.value()
            self.fail("value should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.expire()
            self.fail("expire should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.increment()
            self.fail("increment should be abstract")
        except NotImplementedError:
            pass


class TestThreadedCounter(TestCase):
    """
    ThreadedCounter Tests
    """

    @patch.object(ThreadedCounter, '_threaded_start', side_effect=lambda: None)
    def test_cleanup_thread_resilience(self,  *args, **kwargs):
        # test cleanup thread resilience to Redis Exceptions

        redis_conn = MagicMock()
        tc = ThreadedCounter(start_time=1442671176, cycle_time=1, keep_max=1)  # Initialize the counter
        tc.setup(redis_conn=redis_conn)  # The thread ready but not started since _threaded_start is mock patched

        # Check that a non redis exception kills the thread (assurance that the correct method is tested)
        tc.expire = MagicMock(side_effect=Exception("1"))
        try:
            tc._do_thread_work()
            # this should NOT be reached
            self.assertTrue(False)
        except Exception as e:
            # this should be reached
            self.assertEqual(str(e), "1")

        # Check that a redis exception doesn't kill the thread
        tc.expire = MagicMock(side_effect=redis.RedisError())
        try:
            tc._do_thread_work()
            # this should be reached
            self.assertTrue(True)
        except:
            # this should NOT be reached
            self.assertTrue(False)


