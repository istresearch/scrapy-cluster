# Scrapy Cluster UI test

## Usage 
`pip install -r requirements.txt`

## to run tests

`ui_test.sh`


## Settings
Update the settings.py file 

* WEBDRIVER_TYPE : Chrome| Firefox
* WEBDRIVER_PATH : None (if the webdriver in added in PATH) | Path to the driver

### Note:
* We can run the test without running all the apps, however we need to consider the below in mind. 

* If we run only UI + Rest service, except 2 tests test_scrapy_cluster_paneland test_submit_with_info in
indexpage_test.py all will pass. 

* If we run entire cluster all the tests will pass.


 
