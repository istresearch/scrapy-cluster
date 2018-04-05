#!/bin/bash

set -e

# Build Dockerfiles for Scrapy Cluster
sudo docker build --rm=true --file docker/utils/$dockerfile_name --tag=istresearch/scrapy-cluster:utils-test .
sudo docker build --rm=true --file docker/kafka-monitor/$dockerfile_name --tag=istresearch/scrapy-cluster:kafka-monitor-test .
sudo docker build --rm=true --file docker/redis-monitor/$dockerfile_name --tag=istresearch/scrapy-cluster:redis-monitor-test .
sudo docker build --rm=true --file docker/crawler/$dockerfile_name --tag=istresearch/scrapy-cluster:crawler-test .
sudo docker build --rm=true --file docker/rest/$dockerfile_name --tag=istresearch/scrapy-cluster:rest-test .
sudo docker build --rm=true --file docker/ui/$dockerfile_name --tag=istresearch/scrapy-cluster:ui-test .

# run docker compose up for docker tests
sudo docker-compose -f travis/docker-compose.test.yml up -d

# waiting 10 secs for fully operational cluster
sleep 10

# run docker unit and integration tests for each component
sudo docker-compose -f travis/docker-compose.test.yml exec utils ./run_docker_tests.sh redis 6379 zookeeper:2181
sudo docker-compose -f travis/docker-compose.test.yml exec kafka_monitor ./run_docker_tests.sh
sudo docker-compose -f travis/docker-compose.test.yml exec redis_monitor ./run_docker_tests.sh
sudo docker-compose -f travis/docker-compose.test.yml exec crawler ./run_docker_tests.sh
sudo docker-compose -f travis/docker-compose.test.yml exec rest ./run_docker_tests.sh
sudo docker-compose -f travis/docker-compose.test.yml exec ui ./run_docker_tests.sh

# spin down compose
sudo docker-compose -f travis/docker-compose.test.yml down

# ---- Everything passed, now push to Dockerhub ------

if [ "$TRAVIS_BRANCH" = "dev" ] && [ "$TRAVIS_PULL_REQUEST" = "false" ] && [ "$TRAVIS_EVENT_TYPE" != "cron" ]; then
    # build 'dev' docker images for dockerhub
    sudo docker build --rm=true --file docker/kafka-monitor/$dockerfile_name --tag=istresearch/scrapy-cluster:kafka-monitor-$docker_tag_suffix .
    sudo docker build --rm=true --file docker/redis-monitor/$dockerfile_name --tag=istresearch/scrapy-cluster:redis-monitor-$docker_tag_suffix .
    sudo docker build --rm=true --file docker/crawler/$dockerfile_name --tag=istresearch/scrapy-cluster:crawler-$docker_tag_suffix .
    sudo docker build --rm=true --file docker/rest/$dockerfile_name --tag=istresearch/scrapy-cluster:rest-$docker_tag_suffix .
    sudo docker build --rm=true --file docker/ui/$dockerfile_name --tag=istresearch/scrapy-cluster:ui-$docker_tag_suffix .

    # remove 'test' images
    sudo docker rmi istresearch/scrapy-cluster:utils-test
    sudo docker rmi istresearch/scrapy-cluster:kafka-monitor-test
    sudo docker rmi istresearch/scrapy-cluster:redis-monitor-test
    sudo docker rmi istresearch/scrapy-cluster:crawler-test
    sudo docker rmi istresearch/scrapy-cluster:rest-test
    sudo docker rmi istresearch/scrapy-cluster:ui-test

    # log into docker
    sudo docker login -u="$DOCKER_USERNAME" -p="$DOCKER_PASSWORD"

    # push new containers
    sudo docker push istresearch/scrapy-cluster
fi
