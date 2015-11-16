Crawling Responsibly
====================

Scrapy Cluster is a very high throughput web crawling architecture that allows you to spread the web crawling load across an arbitrary number of machines. It is up the the end user to scrape pages responsibly, and to not crawl sites that do not want to be crawled. As a start, most sites today have a `robots.txt <http://www.robotstxt.org/robotstxt.html>`_ file that will tell you how to crawl the site, how often, and where not to go.

You can very easily max out your internet pipe(s) on your crawling machines by feeding them high amounts of crawl requests. In regular use we have seen a single machine with five crawlers running sustain almost 1000 requests per minute! We were not banned from any site during that test, simply because we obeyed every site's robots.txt file and only crawled at a rate that was safe for any single site.

Abuse of Scrapy Cluster can have the following things occur:

- An investigation from your ISP about the amount of data you are using

- Exceeding the data cap of your ISP

- Semi-permanent and permanent bans of your IP Address from sites you crawl too fast

**With great power comes great responsibility.**