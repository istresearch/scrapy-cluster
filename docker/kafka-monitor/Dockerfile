FROM python:2.7
MAINTAINER Madison Bahmer scrapy-cluster-tech@istresearch.com

# os setup
RUN apt-get update
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# install requirements
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# move codebase over
COPY kafka-monitor /usr/src/app

# scutils dev version install (not in pip yet)
COPY utils /usr/src/app/utils
RUN pip uninstall scutils -y
WORKDIR /usr/src/app/utils
RUN python setup.py install
WORKDIR /usr/src/app

# override settings via localsettings.py
COPY docker/kafka-monitor/settings.py /usr/src/app/localsettings.py

# set up environment variables

# run command
CMD ["python", "kafka_monitor.py", "run"]