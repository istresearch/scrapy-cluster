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


from selenium import webdriver
import chromedriver_binary

from settings import *
from utils import  *


class TestAdminUIService(TestCase):

    # random port number for local connections
    port_number = 52976
    rest_port_number = 52977

    @classmethod
    def setUpClass(cls):
        cls.driver = get_webdriver()

        cls.admin_ui_service = AdminUIService("localsettings.py")
        cls.admin_ui_service.setup()
        cls.admin_ui_service.settings['FLASK_PORT'] = cls.port_number

        def run_server():
            cls.admin_ui_service.run()

        cls._server_thread = Thread(target=run_server)
        cls._server_thread.setDaemon(True)
        cls._server_thread.start()

        cls.ui_url =  'http://127.0.0.1:{p}'.format(p=cls.port_number)

        # sleep 10 seconds for everything to boot up
        time.sleep(10)


    def test_status(self):
        r = requests.get(self.ui_url)
        results = r.content
        self.assertIn(b"<title>Scrapy Cluster</title>", results)


    def test_scrapy_cluster_panel(self):
        """
        If all the 3 services are running it should return 3 success flag
        :return:
        """

        self.driver.get(self.ui_url)
        stats_clmn = self.driver.find_elements_by_css_selector("div.panel-success")
        self.assertEqual(
            3,
            len(stats_clmn))

    def test_submit_without_info(self):
        """
        Pressing Submit button without any value
        :return:
        """
        self.driver.get(self.ui_url)

        self.driver.find_element_by_css_selector("button.btn-primary").click()

        stats_clmn = self.driver.find_element_by_css_selector("ul.flashes")

        self.assertEqual(
            stats_clmn.text,
            'Submit failed')

    def test_submit_with_info(self):
        """
        Pressing Submit button with necessary value
        :return:
        """

        self.driver.get(self.ui_url)

        url =self.driver.find_element_by_name('url')
        url.send_keys("http://dmoztools.net")
        crawlid =self.driver.find_element_by_name('crawlid')
        crawlid.send_keys('1234')
        depth =self.driver.find_element_by_name('depth')
        depth.send_keys('1')
        priority =self.driver.find_element_by_name('priority')
        priority.send_keys('1')

        self.driver.find_element_by_css_selector("button.btn-primary").click()

        stats_clmn = self.driver.find_element_by_css_selector("ul.flashes")

        self.assertEqual(True, True if "Success" not in stats_clmn.text else False )

    def test_scrapy_cluster_crawlerpage_panel(self):
        """
        This will navigate to the Crawler page by clicking the Href
        Check the Plot tile
        :return:
        """

        self.driver.get(self.ui_url)
        self.driver.find_elements_by_css_selector("li")[4].click()
        stats_clmn = self.driver.find_element_by_css_selector("text.gtitle")
        self.assertEqual(
            stats_clmn.text,
            "Backlog")

    def test_scrapy_cluster_kafkapage_panel(self):
        self.driver.get(self.ui_url)

        self.driver.find_elements_by_css_selector("li")[2].click()
        stats_clmn = self.driver.find_element_by_css_selector("text.gtitle")

        self.assertEqual(
            stats_clmn.text,
            "Total Requests handled by Kafka Monitor")


    def test_scrapy_cluster_redispage_panel(self):
        self.driver.get(self.ui_url)
        self.driver.find_elements_by_css_selector("li")[3].click()

        stats_clmn = self.driver.find_element_by_css_selector("text.gtitle")

        self.assertEqual(
            stats_clmn.text,
            "Total Requests handled by Redis Monitor")


    @classmethod
    def tearDownClass(cls):
        cls.admin_ui_service.close()
        cls.driver.quit()


if __name__ == '__main__':
    unittest.main()
