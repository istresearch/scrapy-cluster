FROM python:2.7
MAINTAINER Madison Bahmer <madison.bahmer@istresearch.com>

# os setup
RUN apt-get update && apt-get -y install \
  python-lxml \
  build-essential \
  libssl-dev \
  libffi-dev \
  python-dev \
  libxml2-dev \
  libxslt1-dev \
  && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Set up supervisord
RUN pip install supervisor
COPY docker/supervisord.conf /etc/supervisor/supervisord.conf
RUN mkdir -p /var/log/supervisor
CMD ["/usr/local/bin/supervisord"]

# install requirements
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# move codebase over
COPY crawler /usr/src/app

# scutils dev version install (not in pip yet)
COPY utils /usr/src/app/utils
RUN pip uninstall scutils -y
WORKDIR /usr/src/app/utils
RUN python setup.py install
WORKDIR /usr/src/app

# setup up process to run under supervisord
COPY docker/crawler/sc-crawler-supervisord.conf /etc/supervisor/conf.d/sc-crawler-supervisord.conf

# override settings via localsettings.py
COPY docker/crawler/settings.py /usr/src/app/crawling/localsettings.py

# set up environment variables
ENV NUM_PROCS=1
