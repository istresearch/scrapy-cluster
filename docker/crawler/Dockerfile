FROM python:2.7

# os setup
RUN apt-get update
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Set up supervisord
RUN pip install supervisor
COPY ../supervisord.conf /etc/supervisor/supervisord.conf
RUN mkdir -p /var/log/supervisor
CMD ["/usr/local/bin/supervisord"]

# install requirements
COPY ../../requirements.txt /usr/src/app/
#RUN pip install --no-cache-dir -r requirements.txt

# move codebase over
#COPY . /usr/src/app

# scutils dev version install (not in pip yet)
RUN pip uninstall scutils -y
WORKDIR /usr/src/app/utils
RUN python setup.py install --pre

# setup up process to run under supervisord
#COPY sc-kafka-monitor-supervisord.conf /etc/supervisor/conf.d/cooper-supervisord.conf

# set up environment variables
