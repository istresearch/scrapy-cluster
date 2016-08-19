FROM python:2.7
MAINTAINER Madison Bahmer scrapy-cluster-tech@istresearch.com

# os setup
RUN apt-get update
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Set up supervisord
RUN pip install supervisor
COPY docker/supervisord.conf /etc/supervisord.conf
RUN mkdir -p /var/log/supervisor
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisord.conf"]

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

# setup up process to run under supervisord
COPY docker/kafka-monitor/sc-kafka-monitor-supervisord.conf /etc/supervisor/conf.d/sc-kafka-monitor-supervisord.conf

# override settings via localsettings.py
COPY docker/kafka-monitor/settings.py /usr/src/app/localsettings.py

# set up environment variables
ENV NUM_PROCS=1