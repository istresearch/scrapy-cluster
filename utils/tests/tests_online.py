'''
Online utils test
'''
import unittest
from unittest import TestCase
import mock
from mock import MagicMock

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from redis_queue import RedisQueue
from redis_queue import RedisPriorityQueue
from redis_queue import RedisStack

from redis.exceptions import WatchError
import redis
import argparse

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
        item1 = {"stuff":'a', "blah":2}
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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Online depployement Test"\
                                     " Script for Utils")
    parser.add_argument('-r', '--redis-host', action='store', required=True,
                        default='localhost', help="The Redis host ip")
    parser.add_argument('-p', '--redis-port', action='store', default='6379',
                        help="The Redis port")

    args = vars(parser.parse_args())
    redis_conn = redis.Redis(host=args['redis_host'], port=args['redis_port'])

    # build testing suite
    suite = unittest.TestSuite()
    suite.addTest(TestRedisFifoQueue('test_fifo_queue', redis_conn))
    suite.addTest(TestRedisPriorityQueue('test_priority_queue', redis_conn))
    suite.addTest(TestRedisStack('test_stack', redis_conn))

    unittest.TextTestRunner(verbosity=2).run(suite)