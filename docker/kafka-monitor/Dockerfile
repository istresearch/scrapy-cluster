FROM python:2.7
MAINTAINER Madison Bahmer scrapy-cluster-tech@istresearch.com

# os setup
RUN apt-get update
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# install requirements
COPY kafka-monitor/requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# move codebase over
COPY kafka-monitor /usr/src/app

# override settings via localsettings.py
COPY docker/kafka-monitor/settings.py /usr/src/app/localsettings.py

# copy testing script into container
COPY docker/run_docker_tests.sh /usr/src/app/run_docker_tests.sh

# set up environment variables

# run command
CMD ["python", "kafka_monitor.py", "run"]