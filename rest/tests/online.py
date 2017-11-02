'''
Online tests
'''
import unittest
from unittest import TestCase
from mock import MagicMock

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from rest_service import RestService
import time
import requests
from threading import Thread


class TestRestService(TestCase):

    # random port number for local connections
    port_number = 62976

    def setUp(self):
        self.rest_service = RestService("localsettings.py")
        self.rest_service.setup()
        self.rest_service.settings['FLASK_PORT'] = self.port_number

        def run_server():
            self.rest_service.run()

        self._server_thread = Thread(target=run_server)
        self._server_thread.setDaemon(True)
        self._server_thread.start()

        # sleep 10 seconds for everything to boot up
        time.sleep(10)

    def test_status(self):
        r = requests.get('http://127.0.0.1:{p}'.format(p=self.port_number))
        results = r.json()

        self.assertEqual(results['node_health'], 'GREEN')

    def tearDown(self):
        self.rest_service.close()

if __name__ == '__main__':
    unittest.main()
