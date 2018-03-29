import unittest
from selenium import webdriver
from .settings import *
from .utils import  *

class CrawlerPageTest(unittest.TestCase):
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

    def test_scrapy_cluster_panel(self):
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