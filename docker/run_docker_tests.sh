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

python tests/online.py -v
if [ $? -eq 1 ]; then
    echo "integration tests failed"
    exit 1
fi
