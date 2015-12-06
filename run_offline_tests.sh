#!/bin/bash
cd utils
python tests/tests_offline.py -v
if [ $? -eq 1 ]; then
    echo "utils tests failed"
    exit 1
fi
cd ../kafka-monitor
python tests/tests_offline.py -v
if [ $? -eq 1 ]; then
    echo "kafka-monitor tests failed"
    exit 1
fi
cd ../redis-monitor
python tests/tests_offline.py -v
if [ $? -eq 1 ]; then
    echo "redis-monitor tests failed"
    exit 1
fi
cd ../crawler
python tests/tests_offline.py -v
if [ $? -eq 1 ]; then
    echo "crawler tests failed"
    exit 1
fi
