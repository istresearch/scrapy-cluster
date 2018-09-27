'''
Online utils test
'''
from __future__ import division
from builtins import range
from past.utils import old_div
from builtins import object
import unittest
from unittest import TestCase
from mock import MagicMock
import time
import sys

import redis
import argparse
from kazoo.client import KazooClient

from scutils.redis_queue import RedisQueue, RedisPriorityQueue, RedisStack

from scutils.stats_collector import (ThreadedCounter, TimeWindow,
                                     RollingTimeWindow, Counter, UniqueCounter,
                                     HyperLogLogCounter, BitMapCounter)
from scutils.zookeeper_watcher import ZookeeperWatcher


class RedisMixin(object):

    def __init__(self, name, redis_conn):
        self.redis_conn = redis_conn
        TestCase.__init__(self, name)


class QueueMixin(RedisMixin, object):

    queue_class = None

    def setUp(self):
        self.queue = self.queue_class(self.redis_conn, 'key')


class TestRedisFifoQueue(QueueMixin, TestCase):

    queue_class = RedisQueue

    def test_fifo_queue(self):
        item1 = {"stuff": 'a', "blah": 2}
        item2 = 123
        item3 = "dohrayme"

        self.queue.push(item1)
        self.queue.push(item2)
        self.queue.push(item3)

        self.assertEqual(item1, self.queue.pop())
        self.assertEqual(item2, self.queue.pop())
        self.assertEqual(item3, self.queue.pop())


class TestRedisPriorityQueue(QueueMixin, TestCase):

    queue_class = RedisPriorityQueue

    def test_priority_queue(self):
        # Highest to lowest priority
        item1 = ['a', 'b', 'c']
        item2 = 123
        item3 = "dohrayme"

        self.queue.push(item1, 3)
        self.queue.push(item2, 1)
        self.queue.push(item3, 2)

        self.assertEqual(item1, self.queue.pop())
        self.assertEqual(item3, self.queue.pop())
        self.assertEqual(item2, self.queue.pop())


class TestRedisStack(QueueMixin, TestCase):

    queue_class = RedisStack

    def test_stack(self):
        item1 = ['a', 'b', 'c']
        item2 = 123
        item3 = "dohrayme"

        self.queue.push(item1)
        self.queue.push(item2)
        self.queue.push(item3)

        self.assertEqual(item3, self.queue.pop())
        self.assertEqual(item2, self.queue.pop())
        self.assertEqual(item1, self.queue.pop())


class TestStatsThreaded(RedisMixin, TestCase):

    def test_set_key(self):
        tc = ThreadedCounter(start_time=1442671176)
        self.assertEqual('default_counter', tc.get_key())

        tc.roll = True
        tc.key = 'myKey'
        tc._set_key()
        self.assertEqual('myKey:2015-09-19_13:59:36', tc.get_key())

    def test_is_expired(self):
        # test rolling the key we are using
        tc = ThreadedCounter(start_time=1442671176, window=5)
        tc._time = MagicMock(return_value=1442671177)
        self.assertFalse(tc.is_expired())

        tc._time = MagicMock(return_value=1442671182)
        self.assertTrue(tc.is_expired())

    def test_threading(self):
        # this test ensures the thread can start and stop
        tc = ThreadedCounter(start_time=1442671176, cycle_time=1)
        tc.expire = MagicMock()
        tc.setup(redis_conn=self.redis_conn)
        time.sleep(1)
        tc.stop()

    def test_purge_old(self):
        # test removing old keys
        tc = ThreadedCounter(keep_max=1)
        tc.keep_max = 1
        tc.redis_conn = self.redis_conn
        self.redis_conn.set('default_counter:2015-09', 'stuff')
        self.redis_conn.set('default_counter:2015-10', 'stuff2')

        tc.purge_old()
        self.assertEqual(['default_counter:2015-10'],
                         self.redis_conn.keys(tc.get_key() + ':*'))

        self.redis_conn.delete('default_counter:2015-10')

    def tearDown(self):
        keys = self.redis_conn.keys('default_counter:*')
        while len(keys) > 0:
            key = keys.pop()
            self.redis_conn.delete(key)


class CleanMixin(object):

    def clean_keys(self, key):
        keys = self.redis_conn.keys(key + '*')
        while len(keys) > 0:
            key = keys.pop()
            self.redis_conn.delete(key)


class TestStatsTimeWindow(RedisMixin, TestCase, CleanMixin):

    def test_window(self):
        counter = TimeWindow(key='test_key', cycle_time=.1, window=1)
        counter.setup(self.redis_conn)
        counter.increment()
        counter.increment()
        counter.increment()
        time.sleep(1.1)
        counter.increment()
        counter.stop()
        self.assertEqual(counter.value(), 3)

        self.clean_keys(counter.key)

    def test_roll_window(self):
        counter = TimeWindow(key='test_key', cycle_time=.01, window=1,
                             roll=True)
        counter.setup(self.redis_conn)
        counter.increment()
        counter.increment()
        counter.increment()
        time.sleep(1.5)
        counter.increment()
        counter.increment()
        counter.stop()

        keys = self.redis_conn.keys('test_key:*')
        keys.sort()
        self.assertEqual(len(keys), 2)
        self.assertEqual(self.redis_conn.zcard(keys[0]), 3)
        self.assertEqual(counter.value(), 2)
        counter.stop()
        self.clean_keys(counter.key)


class TestStatsRollingTimeWindow(RedisMixin, TestCase, CleanMixin):

    def test_rolling_window(self):
        # rough sleep to get us back on track
        time.sleep(5 - (int(time.time()) % 5))
        counter = RollingTimeWindow(key='test_key', cycle_time=.01, window=5)
        counter.setup(self.redis_conn)
        counter.increment()
        counter.increment()
        time.sleep(3)
        counter.increment()
        counter.increment()
        time.sleep(3)
        # at this point the first 2 counts have expired
        counter.increment()
        self.assertEqual(counter.value(), 3)
        time.sleep(5.1)
        # now everything has expired
        self.assertEqual(counter.value(), 0)
        # check to ensure counter is still working
        counter.increment()
        self.assertEqual(counter.value(), 1)
        counter.stop()
        self.clean_keys(counter.key)


class TestStatsCounter(RedisMixin, TestCase, CleanMixin):

    def test_generic_counter(self):
        counter = Counter(key='test_key')
        counter.setup(redis_conn=self.redis_conn)
        i = 0
        while i < 10000:
            counter.increment()
            i += 1

        self.assertEqual(10000, counter.value())
        counter.stop()
        self.clean_keys(counter.key)

    def test_roll_generic_counter(self):
        # rough sleep to get us back on track
        time.sleep(2 - (int(time.time()) % 2))
        counter = Counter(key='test_key', window=2, cycle_time=.1, roll=True)
        counter.setup(redis_conn=self.redis_conn)
        i = 0
        while i < 100:
            counter.increment()
            i += 1
        self.assertEqual(counter.value(), 100)
        time.sleep(3)
        # now the counter should have rolled
        i = 0
        while i < 50:
            counter.increment()
            i += 1
        self.assertEqual(counter.value(), 50)
        counter.stop()
        self.clean_keys(counter.key)


class TestStatsUniqueCounter(RedisMixin, TestCase, CleanMixin):

    def test_uniques(self):
        counter = UniqueCounter(key='test_key')
        counter.setup(redis_conn=self.redis_conn)

        i = 0
        while i < 1000:
            counter.increment(i % 100)
            i += 1
        self.assertEqual(counter.value(), 100)
        counter.stop()
        self.clean_keys(counter.key)

    def test_roll_uniques(self):
        # rough sleep to get us back on track
        time.sleep(2 - (int(time.time()) % 2))
        counter = UniqueCounter(key='test_key', window=2, cycle_time=.1,
                                roll=True)
        counter.setup(redis_conn=self.redis_conn)
        i = 0
        while i < 100:
            counter.increment(i % 10)
            i += 1
        self.assertEqual(counter.value(), 10)
        time.sleep(3)
        # now the counter should have rolled
        i = 0
        while i < 50:
            counter.increment(i % 10)
            i += 1
        self.assertEqual(counter.value(), 10)
        counter.stop()
        self.clean_keys(counter.key)


class TestStatsHyperLogLogCounter(RedisMixin, TestCase, CleanMixin):

    tolerance = 2   # percent

    def get_percent_diff(self, value, actual):
        return abs(actual - value) / (old_div((value + actual), 2.0)) * 100.0

    def test_hll_counter(self):
        counter = HyperLogLogCounter(key='test_key')
        counter.setup(redis_conn=self.redis_conn)
        for n in range(3):
            i = 0
            while i < 10010 * (n + 1):
                counter.increment(i % (5000 * (n + 1)))
                i += 1

            value = 5000 * (n + 1)
            actual = counter.value()
            diff = self.get_percent_diff(value, actual)
            self.assertLessEqual(diff, self.tolerance)
            self.clean_keys(counter.key)

        counter.stop()

    def test_roll_hll_counter(self):
        # rough sleep to get us back on track
        time.sleep(5.0 - (time.time() % 5.0))
        counter = HyperLogLogCounter(key='test_key', window=5, roll=True,
                                     cycle_time=.1,)
        counter.setup(redis_conn=self.redis_conn)
        i = 0
        while i < 5010:
            counter.increment(i % 1010)
            i += 1
        value = 1010
        actual = counter.value()
        diff = self.get_percent_diff(value, actual)
        self.assertLessEqual(diff, self.tolerance)
        self.clean_keys(counter.key)
        # rough sleep to get us back on track
        time.sleep(5.0 - (time.time() % 5.0))
        # we should be on to a new counter window by now
        i = 0
        while i < 5010:
            counter.increment(i % 3010)
            i += 1
        value = 3010
        actual = counter.value()
        diff = self.get_percent_diff(value, actual)
        self.assertLessEqual(diff, self.tolerance)
        counter.stop()
        self.clean_keys(counter.key)


class TestStatsBitMapCounter(RedisMixin, TestCase, CleanMixin):

    def test_bitmap_counter(self):
        counter = BitMapCounter(key='test_key')
        counter.setup(redis_conn=self.redis_conn)

        counter.increment(0)
        counter.increment(1)
        counter.increment(5)
        counter.increment(0)
        self.assertEqual(3, counter.value())
        counter.stop()
        self.clean_keys(counter.key)

    def test_roll_bitmap_counter(self):
        # rough sleep to get us back on track
        time.sleep(2 - (int(time.time()) % 2))
        counter = BitMapCounter(key='test_key', window=2, cycle_time=.1,
                                roll=True)
        counter.setup(redis_conn=self.redis_conn)

        counter.increment(0)
        counter.increment(1)
        counter.increment(0)
        self.assertEqual(2, counter.value())
        time.sleep(3)
        counter.increment(0)
        self.assertEqual(1, counter.value())
        counter.stop()
        self.clean_keys(counter.key)


class TestZookeeperWatcher(TestCase):
    def __init__(self, name, hosts):
        self.hosts = hosts
        self.file_path = '/test_path'
        self.file_data = 'test_data'
        self.pointer_path = '/test_pointer'
        self.pointer_data = self.file_path
        TestCase.__init__(self, name)

    def setUp(self):
        self.zoo_client = KazooClient(hosts=self.hosts)
        self.zoo_client.start()
        # prepare data
        self.zoo_client.ensure_path(self.file_path)
        self.zoo_client.set(self.file_path, self.file_data.encode('utf-8'))
        self.zoo_client.ensure_path(self.pointer_path)
        self.zoo_client.set(self.pointer_path,
                            self.pointer_data.encode('utf-8'))

        self.zoo_watcher = ZookeeperWatcher(hosts=self.hosts,
                                            filepath=self.file_path,
                                            pointer=False,
                                            ensure=False,
                                            valid_init=True)

    def test_ping(self):
        self.assertTrue(self.zoo_watcher.ping())

    def test_get_file_contents(self):
        pointer_zoo_watcher = ZookeeperWatcher(hosts=self.hosts,
                                               filepath=self.pointer_path,
                                               pointer=True,
                                               ensure=False,
                                               valid_init=True)

        self.assertEqual(self.zoo_watcher.get_file_contents(), self.file_data)
        self.assertEqual(pointer_zoo_watcher.get_file_contents(),
                          self.file_data)
        self.assertEqual(pointer_zoo_watcher.get_file_contents(True),
                          self.pointer_data)

        pointer_zoo_watcher.close()

    def tearDown(self):
        self.zoo_watcher.close()

        self.zoo_client.ensure_path(self.file_path)
        self.zoo_client.delete(self.file_path)
        self.zoo_client.ensure_path(self.pointer_path)
        self.zoo_client.delete(self.pointer_path)
        self.zoo_client.stop()
        self.zoo_client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Online deployment Test"
                                     " Script for Utils")
    parser.add_argument('-r', '--redis-host', action='store',
                        default='localhost', help="The Redis host ip")
    parser.add_argument('-p', '--redis-port', action='store', default='6379',
                        help="The Redis port")
    parser.add_argument('-P', '--redis-password', action='store', default=None,
                        help="The Redis password")
    parser.add_argument('-z', '--zoo-keeper', action='store',
                        default='localhost:2181',
                        help="The Zookeeper connection <host>:<port>")

    args = vars(parser.parse_args())
    redis_conn = redis.Redis(host=args['redis_host'], port=args['redis_port'],
                             password=args['redis_password'], decode_responses=True)

    # build testing suite
    suite = unittest.TestSuite()

    # moved to the top to help get better consistency
    suite.addTest(TestStatsHyperLogLogCounter('test_hll_counter', redis_conn))
    suite.addTest(TestStatsHyperLogLogCounter('test_roll_hll_counter',
                  redis_conn))

    suite.addTest(TestRedisFifoQueue('test_fifo_queue', redis_conn))
    suite.addTest(TestRedisPriorityQueue('test_priority_queue', redis_conn))
    suite.addTest(TestRedisStack('test_stack', redis_conn))

    suite.addTest(TestStatsThreaded('test_set_key', redis_conn))
    suite.addTest(TestStatsThreaded('test_is_expired', redis_conn))
    suite.addTest(TestStatsThreaded('test_threading', redis_conn))
    suite.addTest(TestStatsThreaded('test_purge_old', redis_conn))

    suite.addTest(TestStatsTimeWindow('test_window', redis_conn))
    suite.addTest(TestStatsTimeWindow('test_roll_window', redis_conn))

    suite.addTest(TestStatsRollingTimeWindow('test_rolling_window',
                  redis_conn))

    suite.addTest(TestStatsCounter('test_generic_counter', redis_conn))
    suite.addTest(TestStatsCounter('test_roll_generic_counter', redis_conn))

    suite.addTest(TestStatsUniqueCounter('test_uniques', redis_conn))
    suite.addTest(TestStatsUniqueCounter('test_roll_uniques', redis_conn))

    suite.addTest(TestStatsBitMapCounter('test_bitmap_counter', redis_conn))
    suite.addTest(TestStatsBitMapCounter('test_roll_bitmap_counter',
                  redis_conn))
    suite.addTest(TestZookeeperWatcher('test_ping', args['zoo_keeper']))
    suite.addTest(TestZookeeperWatcher('test_get_file_contents',
                  args['zoo_keeper']))

    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if len(result.errors) > 0 or len(result.failures) > 0:
        sys.exit(1)
    else:
        sys.exit(0)
