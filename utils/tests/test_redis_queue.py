from builtins import object
from unittest import TestCase
import json
import copy
import pickle
import ujson
import sys

from mock import MagicMock
from scutils.redis_queue import Base, RedisQueue, RedisPriorityQueue, RedisStack


class TestBase(TestCase):

    def setUp(self):
        self.q = Base(MagicMock(), 'k')

    def test_init(self):
        # assert example good encoding
        q = Base(MagicMock(), 'key')
        q1 = Base(MagicMock(), 'key', pickle)
        q2 = Base(MagicMock(), 'key', ujson)
        q3 = Base(MagicMock(), 'key', json)

        # assert bad encodings
        with self.assertRaises(NotImplementedError) as e:
            q2 = Base(MagicMock(), 'key', copy)

    def test_encode(self):
        q = Base(MagicMock(), 'key', pickle)
        # python pickling is different between versions
        data = pickle.dumps('cool', protocol=-1).decode('latin1')
        self.assertEqual(q._encode_item('cool'), data)
        q2 = Base(MagicMock(), 'key', ujson)
        self.assertEqual(q2._encode_item('cool2'), '"cool2"')

    def test_decode(self):
        q = Base(MagicMock(), 'key', pickle)
        self.assertEqual(q._decode_item(u"\x80\x02U\x04coolq\x00."), 'cool')

        q2 = Base(MagicMock(), 'key', ujson)
        self.assertEqual(q2._decode_item('"cool2"'), 'cool2')

    def test_len(self):
        with self.assertRaises(NotImplementedError):
            len(self.q)

    def test_push(self):
        with self.assertRaises(NotImplementedError):
            self.q.push("blah")

    def test_pop(self):
        with self.assertRaises(NotImplementedError):
            self.q.pop()

    def test_clear(self):
        self.q.clear()


class QueueMixin(object):
    queue_class = None

    def setUp(self):
        self.queue = self.queue_class(MagicMock(), 'key', ujson)


class TestRedisQueue(QueueMixin, TestCase):

    queue_class = RedisQueue

    def test_len(self):
        self.assertTrue(hasattr(self.queue, '__len__'))
        len(self.queue)

    def test_push(self):
        self.assertTrue(hasattr(self.queue, 'push'))
        self.queue.push("blah")

    def test_pop(self):
        self.assertTrue(hasattr(self.queue, 'pop'))
        self.queue.server.rpop = MagicMock(return_value='"stuff"')
        self.assertEqual(self.queue.pop(), "stuff")


class TestRedisPriorityQueue(QueueMixin, TestCase):

    queue_class = RedisPriorityQueue

    def test_len(self):
        self.assertTrue(hasattr(self.queue, '__len__'))
        len(self.queue)

    def test_push(self):
        self.assertTrue(hasattr(self.queue, 'push'))
        self.queue.push("blah", 60)

    def test_pop(self):
        self.assertTrue(hasattr(self.queue, 'pop'))
        m = MagicMock()
        m.execute = MagicMock(return_value=[{}, 60])
        self.queue.server.pipeline = MagicMock(return_value=m)
        self.assertEqual(self.queue.pop(), None)


class TestRedisStack(QueueMixin, TestCase):

    queue_class = RedisStack

    def test_len(self):
        self.assertTrue(hasattr(self.queue, '__len__'))
        len(self.queue)

    def test_push(self):
        self.assertTrue(hasattr(self.queue, 'push'))
        self.queue.push("blah")

    def test_pop(self):
        self.assertTrue(hasattr(self.queue, 'pop'))
        self.queue.server.lpop = MagicMock(return_value='"stuff"')
        self.assertEqual(self.queue.pop(), "stuff")
