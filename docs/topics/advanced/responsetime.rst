Response Time
=============

The Scrapy Cluster Response time is dependent on a number of factors:

- How often the Kafka Monitor polls for new messages

- How often any one spider polls redis for new requests

- How many spiders are polling

- How fast the spider can fetch the request

- How fast your item pipeline can get the response into Kafka


With the Kafka Monitor constantly monitoring the incoming topic, there is very little latency for getting a request into the system. The bottleneck occurs mainly in the core Scrapy crawler code.

The more crawlers you have running and spread across the cluster, the lower the average response time will be for a crawler to receive a request. For example if a single spider goes idle and then polls every 5 seconds, you would expect a your maximum response time to be 5 seconds, the minimum response time to be 0 seconds, but on average your response time should be 2.5 seconds for one spider. As you increase the number of spiders in the system the likelihood that one spider is polling also increases, and the cluster performance will go up.

The next bottleneck in response time is how quickly the request can be conducted by Scrapy, which depends on the speed of the internet connection(s) you are running the Scrapy Cluster behind. This is out of control of the Scrapy Cluster itself, but relies heavily on your ISP or other network configuration.

Once your spider has processed the response and yields an item, your item pipeline before the response gets to Kafka may slow your item down. If you are doing complex processing here, it is recommended you move it out of Scrapy and into a larger architecture.

Overall, your cluster response time for brand new crawls on a domain not yet seen is a lot slower than a domain that is already in the crawl backlog. The more Crawlers you have running, the bigger throughput you will be able to achieve.