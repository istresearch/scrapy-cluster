"""
Online tests
"""
import unittest
from unittest import TestCase

import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from ui_service import AdminUIService

import time
import requests

from threading import Thread


class TestAdminUIService(TestCase):

    # random port number for local connections
    port_number = 52976
    rest_port_number = 52977

    def setUp(self):
        self.admin_ui_service = AdminUIService("localsettings.py")
        self.admin_ui_service.setup()
        self.admin_ui_service.settings['FLASK_PORT'] = self.port_number

        def run_server():
            self.admin_ui_service.run()

        self._server_thread = Thread(target=run_server)
        self._server_thread.setDaemon(True)
        self._server_thread.start()

        # sleep 10 seconds for everything to boot up
        time.sleep(10)

    def test_status(self):
        r = requests.get('http://127.0.0.1:{p}'.format(p=self.port_number))
        results = r.content
        self.assertIn(b"<title>Scrapy Cluster</title>", results)

    def tearDown(self):
        self.admin_ui_service.close()

if __name__ == '__main__':
    unittest.main()
