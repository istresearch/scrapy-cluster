#!/bin/bash
cd utils
nosetests -v --with-coverage --cover-erase
if [ $? -eq 1 ]; then
    echo "utils tests failed"
    exit 1
fi
cd ../kafka-monitor
nosetests -v --with-coverage --cover-erase --cover-package=../kafka-monitor/
if [ $? -eq 1 ]; then
    echo "kafka-monitor tests failed"
    exit 1
fi
cd ../redis-monitor
nosetests -v --with-coverage --cover-erase --cover-package=../redis-monitor/
if [ $? -eq 1 ]; then
    echo "redis-monitor tests failed"
    exit 1
fi
cd ../crawler
nosetests -v --with-coverage --cover-erase --cover-package=crawling/
if [ $? -eq 1 ]; then
    echo "crawler tests failed"
    exit 1
fi
cd ../rest
nosetests -v --with-coverage --cover-erase --cover-package=../rest/
if [ $? -eq 1 ]; then
    echo "rest tests failed"
    exit 1
fi
cd ../ui
nosetests -v --with-coverage --cover-erase --cover-package=../ui/
if [ $? -eq 1 ]; then
    echo "ui tests failed"
    exit 1
fi
cd ../
coverage combine crawler/.coverage kafka-monitor/.coverage redis-monitor/.coverage utils/.coverage rest/.coverage ui/.coverage

