import unittest
from selenium import webdriver
from .settings import *
from .utils import  *

class RedisPageTest(unittest.TestCase):
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


    def test_scrapy_cluster_panel(self):
        self.driver.get(UI_URL)
        self.driver.find_elements_by_css_selector("li")[3].click()

        stats_clmn = self.driver.find_element_by_css_selector("text.gtitle")

        self.assertEqual(
            stats_clmn.text,
            "Total Requests handled by Redis Monitor")


    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()