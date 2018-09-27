#!/bin/bash

# Script for testing Scrapy Clusters online setup
# If all tests pass, then your all components appear to be working correctly
# and integrated with all other components

HOST='localhost'
PORT=6379
PASSWORD='None'
ZOOKEEPER_HOST='localhost:2181'

if [ $# -ne 4 ]
  then
    echo "---- Running utils online test with redis on localhost:6379 with password: None and zookeeper on localhost:2181"
    echo "Other usage:"
    echo "    ./bundle.sh <utils_redis_host> <utils_redis_port> <utils_redis_password> <utils_zookeeper_host>"
else
    echo "---- Using custom redis and zookeeper host and port for utils online test"
    HOST=$1
    PORT=$2
    PASSWORD=$3
    ZOOKEEPER_HOST=$4
fi

cd utils
if [ $PASSWORD != 'None' ]; then
    python tests/online.py -r $HOST -p $PORT -P $PASSWORD -z $ZOOKEEPER_HOST
else
    python tests/online.py -r $HOST -p $PORT -z $ZOOKEEPER_HOST
fi
if [ $? -eq 1 ]; then
    echo "utils tests failed"
    exit 1
fi
cd ../kafka-monitor
python tests/online.py -v
if [ $? -eq 1 ]; then
    echo "kafka-monitor tests failed"
    exit 1
fi
cd ../redis-monitor
python tests/online.py -v
if [ $? -eq 1 ]; then
    echo "redis-monitor tests failed"
    exit 1
fi
cd ../crawler
python tests/online.py -v
if [ $? -eq 1 ]; then
    echo "crawler tests failed"
    exit 1
fi
cd ../rest
python tests/online.py -v
if [ $? -eq 1 ]; then
    echo "rest tests failed"
    exit 1
fi
