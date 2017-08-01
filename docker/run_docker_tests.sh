#!/bin/sh

# Script for testing Scrapy Cluster when inside a docker container
# Will run both the offline and online tests for the particular container,
# but does not care about coverage

# If all tests pass, then the component appears to be working correctly
# and integrated

nosetests -v
if [ $? -eq 1 ]; then
    echo "unit tests failed"
    exit 1
fi

# if 3 parameters passed in, then it's util's test
if [ $# -eq 3 ]; then
    python tests/online.py -r $1 -p $2 -z $3
    if [ $? -eq 1 ]; then
        echo "integration tests failed"
        exit 1
    fi
else
    python tests/online.py -v
    if [ $? -eq 1 ]; then
        echo "integration tests failed"
        exit 1
    fi
fi
