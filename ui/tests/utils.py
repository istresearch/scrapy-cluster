import sys
from os import path

from selenium import webdriver

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from settings import *

def get_webdriver():
    print("called")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('headless')
    chrome_options.add_argument('no-sandbox')
    if WEBDRIVER_TYPE == 'Chrome':
        if WEBDRIVER_PATH:
            return webdriver.Chrome(WEBDRIVER_PATH)
        else:
            return webdriver.Chrome(chrome_options=chrome_options)
    elif   WEBDRIVER_TYPE == 'Firefox':
        if WEBDRIVER_PATH:
            return webdriver.Firefox(WEBDRIVER_PATH)
        else:
            return webdriver.Firefox()
