"""
Trendyol Spider

Trendyol Spider module providing three "Category", "ProductList" and "Product" spiders,
Which are used to crawl / scrap data from "trendyol.com" website.

NOTE: This Spider is mainly focused at providing functionality for Scrapy-Cluster tool, 
So it may slightly differ from normal scrapy spiders.
"""

# Import libraries / modules
from crawling.spiders.redis_spider import RedisSpider
from crawling.items import RawResponseItem
from scrapy .http import Request


# Create Spider in Scrapy-Cluster's recommended way - using RedisSpider
class CategorySpider(RedisSpider):
	"""
	A Spider that extracts category list from trendyol homepage 
	and gives them to ProductList Spiders for further processing.
	"""

	# Set spider id / name
	name = "trendyol_category"

	def __init__(self, *args, **kwargs):
		# Initialize RedisSpider
		super(CategorySpider, self).__init__(*args, **kwargs)

		# Log spider start
		self._logger.info("Started Category Spider")

	# Start parsing the response
	def parse(self, response):
		# Log parsing start
		self._logger.info("Crawled URL: ". response.request.url)
		self.logger.info("Parsing the response...")

		# Capture raw response
		item = RawResponseItem()

		# Populated from response.meta
		item['appid'] = response.meta['appid']
		item['crawlid'] = response.meta['crawlid']
		item['attrs'] = response.meta['attrs']

        # Populated from raw HTTP response
        item["url"] = response.request.url
        item["response_url"] = response.url
        item["status_code"] = response.status
        item["status_msg"] = "OK"
        item["response_headers"] = self.reconstruct_headers(response)
        item["request_headers"] = response.request.headers
        item["body"] = response.body
        item["encoding"] = response.encoding
        yield item
		# home_soup = BeautifulSoup(response.body.text, 'html.parser')
	 #    cat_list = home_soup.find_all("ul", {'class': 'sub-item-list'})
	 #    subcat_list = []
	 #    for each in cat_list:
	 #        sub_cats = [('https://www.trendyol.com' + subcat.a['href'])
	 #                    for subcat in each.find_all('li')]
	 #        for subcat in sub_cats:
	 #            if subcat in subcat_list:
	 #                sub_cats.remove(subcat)
	 #        subcat_list += sub_cats

