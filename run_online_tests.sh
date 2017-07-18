#!/bin/bash

# Script for testing Scrapy Clusters online setup
# If all tests pass, then your all components appear to be working correctly
# and integrated with all other components

HOST='localhost'
PORT=6379

export PYTHONPATH='.'

if [ $# -ne 2 ]
  then
    echo "---- Running utils online test with localhost 6379"
    echo "Other usage:"
    echo "    ./bundle.sh <utils_redis_host> <utils_redis_port>"
else
    echo "---- Using custom redis host and port for utils online test"
    HOST=$1
    PORT=$2
fi

cd utils
cd ../rest
python tests/online.py -v
if [ $? -eq 1 ]; then
    echo "rest tests failed"
    exit 1
fi
python rest_service.py &
sleep 5
cd ../ui
python tests/online.py -v
if [ $? -eq 1 ]; then
    echo "ui tests failed"
    exit 1
fi
sudo kill $(ps aux | grep 'rest_service.py' | awk '{print $2}')
