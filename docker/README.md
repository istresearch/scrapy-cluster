Docker
======

This folder houses the Dockerfiles and settings associated with Scrapy Cluster.

For more information please check out the [documentation](http://scrapy-cluster.readthedocs.org)

Want to build your own containers? From the root directory of this project run

```
$ docker build -t <your_tag> -f docker/<component>/Dockerfile .

# build the redis monitor on the dev branch
$ docker build -t istresearch/scrapy-cluster:redis-monitor-dev -f docker/redis-monitor/Dockerfile .
```