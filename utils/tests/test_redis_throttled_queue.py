'''
Offline utility tests
'''
from unittest import TestCase
from mock import MagicMock
from redis.exceptions import WatchError
from scutils.redis_throttled_queue import RedisThrottledQueue


class TestUnmoderatedRedisThrottledQueue(TestCase):

    def setUp(self):
        # limit is 2 hits in the window
        self.queue = RedisThrottledQueue(MagicMock(), MagicMock(), 1, 2)

    def test_unmoderated(self):
        # an unmoderated queue is really just testing the number
        # of hits in a given window
        self.queue.redis_conn.zcard = MagicMock(return_value=0)
        self.assertTrue(self.queue.allowed())

        self.queue.redis_conn.zcard = MagicMock(return_value=1)
        self.assertTrue(self.queue.allowed())

        self.queue.redis_conn.zcard = MagicMock(return_value=2)
        self.assertFalse(self.queue.allowed())

        # mock exception raised even with good hits
        self.queue.redis_conn.zcard = MagicMock(return_value=0,
                                                side_effect=WatchError)
        self.assertFalse(self.queue.allowed())


class TestModeratedRedisThrottledQueue(TestCase):

    def setUp(self):
        self.queue = RedisThrottledQueue(MagicMock(), MagicMock(), 4, 2, True)

    def test_moderated(self):
        # a moderated queue should pop ~ every x seconds
        # we already tested the window limit in the unmoderated test
        self.queue.is_moderated = MagicMock(return_value=True)
        self.assertFalse(self.queue.allowed())

        self.queue.is_moderated = MagicMock(return_value=False)
        self.queue.test_hits = MagicMock(return_value=True)
        self.assertTrue(self.queue.allowed())

        # mock exception raised even with good moderation
        self.queue.test_hits = MagicMock(side_effect=WatchError)
        self.assertFalse(self.queue.allowed())

class TestModeratedElasticRedisThrottledQueue(TestCase):

    def setUp(self):
        self.queue = RedisThrottledQueue(MagicMock(), MagicMock(), 4, 2, True,
                                         elastic=True)

    def test_moderated(self):
        # test elastic kick in hasnt happened yet
        self.queue.is_moderated = MagicMock(return_value=True)
        self.queue.elastic_kick_in = 0
        self.assertFalse(self.queue.allowed())

        # kick in overrides, even though we were moderated
        self.queue.elastic_kick_in = self.queue.limit
        self.queue.check_elastic = MagicMock(return_value=True)
        self.queue.test_hits = MagicMock(return_value=True)
        self.assertTrue(self.queue.allowed())
