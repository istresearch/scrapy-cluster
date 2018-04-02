#!/bin/bash
cd scripts

nosetests crawlerpage_test.py
nosetests indexpage_test.py
nosetests kafkamonitor_test.py
nosetests redismonitor_test.py