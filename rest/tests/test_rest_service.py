'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from mock import call
from rest_service import RestService
import mock
import socket
import time


class TestRestService(TestCase):

    def setUp(self):
        self.rest_service = RestService("settings.py")
        # self.redis_monitor = RedisMonitor("settings.py", True)
        # self.redis_monitor.settings = self.redis_monitor.wrapper.load("settings.py")
        # self.redis_monitor.logger = MagicMock()
        pass

    def test_stuff(self):
        pass