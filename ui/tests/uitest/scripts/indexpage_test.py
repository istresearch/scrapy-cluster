import unittest
from selenium import webdriver
from .settings import *
from .utils import  *

class IndexTest(unittest.TestCase):
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