"""
Offline tests
"""
from unittest import TestCase
from mock import MagicMock
import requests

import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from ui_service import AdminUIService


class TestAdminUIService(TestCase):

    def setUp(self):
        self.admin_ui_service = AdminUIService("localsettings.py")
        self.admin_ui_service.settings = self.admin_ui_service.wrapper.load("localsettings.py")
        self.admin_ui_service.logger = MagicMock()

    def test_close(self):
        self.admin_ui_service.close()
        self.assertTrue(self.admin_ui_service.closed)

    # Routes ------------------

    def test_index(self):
        with self.admin_ui_service.app.test_request_context():
            response = requests.Response()
            response.status_code = 400

            self.admin_ui_service._rest_api = MagicMock(return_value={'status':'FAILURE'})
            res = self.admin_ui_service.index()
            d = "<title>Scrapy Cluster</title>"
            self.assertIn(d, res)
