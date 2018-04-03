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
from settings import *
from utils import  *


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



class IndexTest(TestCase):
    """
    This is to test the Index page in Scrapy cluster UI.
    """

    @classmethod
    def setUpClass(cls):
        cls.driver = get_webdriver()

    def test_title(self):
        """
        This test is to check the title of the page.
        :return:
        """

        self.driver.get(UI_URL)
        self.assertEqual(self.driver.title,'Scrapy Cluster')


    def test_scrapy_cluster_panel(self):
        """
        If all the 3 services are running it should return 3 success flag
        :return:
        """

        self.driver.get(UI_URL)
        stats_clmn = self.driver.find_elements_by_css_selector("div.panel-success")
        self.assertEqual(
            3,
            len(stats_clmn))

    def test_submit_without_info(self):
        """
        Pressing Submit button without any value
        :return:
        """
        self.driver.get(UI_URL)

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

        self.driver.get(UI_URL)

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


    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()



class CrawlerPageTest(TestCase):
    """
    This is to test the Crawler page in Scrapy cluster UI.
    """

    @classmethod
    def setUpClass(cls):
        cls.driver = get_webdriver()

    def test_title(self):
        """
        This will navigate to the Crawler page by clicking the Href
        Check the title
        :return:
        """

        self.driver.get(UI_URL)
        self.driver.find_elements_by_css_selector("li")[4].click()
        self.assertEqual(self.driver.title,'Scrapy Cluster')

    def test_scrapy_cluster_crawlerpage_panel(self):
        """
        This will navigate to the Crawler page by clicking the Href
        Check the Plot tile
        :return:
        """

        self.driver.get(UI_URL)
        self.driver.find_elements_by_css_selector("li")[4].click()
        stats_clmn = self.driver.find_element_by_css_selector("text.gtitle")
        self.assertEqual(
            stats_clmn.text,
            "Backlog")

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()



class KafkaPageTest(TestCase):
    """
    This is to test the Kafka page in Scrapy cluster UI.
    """

    @classmethod
    def setUpClass(cls):
       cls.driver = get_webdriver()

    def test_title(self):
        self.driver.get(UI_URL)
        self.driver.find_elements_by_css_selector("li")[2].click()
        self.assertEqual(self.driver.title,'Scrapy Cluster')

    def test_scrapy_cluster_kafkapage_panel(self):
        self.driver.get(UI_URL)

        self.driver.find_elements_by_css_selector("li")[2].click()
        stats_clmn = self.driver.find_element_by_css_selector("text.gtitle")

        self.assertEqual(
            stats_clmn.text,
            "Total Requests handled by Kafka Monitor")


    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()


class RedisPageTest(TestCase):
    """
    This is to test the Redis page in Scrapy cluster UI.
    """

    @classmethod
    def setUpClass(cls):
        cls.driver = get_webdriver()

    def test_title(self):
        self.driver.get(UI_URL)
        self.driver.find_elements_by_css_selector("li")[3].click()

        self.assertEqual(self.driver.title,'Scrapy Cluster')


    def test_scrapy_cluster_redispage_panel(self):
        self.driver.get(UI_URL)
        self.driver.find_elements_by_css_selector("li")[3].click()

        stats_clmn = self.driver.find_element_by_css_selector("text.gtitle")

        self.assertEqual(
            stats_clmn.text,
            "Total Requests handled by Redis Monitor")


    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

if __name__ == '__main__':
    suite = unittest.TestSuite()

    suite.addTest(TestAdminUIService('test_status'))

    suite.addTest(IndexTest('test_title'))
    suite.addTest(IndexTest('test_scrapy_cluster_panel'))
    suite.addTest(IndexTest('test_submit_without_info'))
    suite.addTest(IndexTest('test_submit_with_info'))

    suite.addTest(CrawlerPageTest('test_title'))
    suite.addTest(CrawlerPageTest('test_scrapy_cluster_crawlerpage_panel'))

    suite.addTest(KafkaPageTest('test_title'))
    suite.addTest(KafkaPageTest('test_scrapy_cluster_kafkapage_panel'))

    suite.addTest(RedisPageTest('test_title'))
    suite.addTest(RedisPageTest('test_scrapy_cluster_redispage_panel'))
    
    
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if len(result.errors) > 0 or len(result.failures) > 0:
        sys.exit(1)
    else:
        sys.exit(0)