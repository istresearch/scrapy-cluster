FROM python:2.7.12-alpine
MAINTAINER Madison Bahmer <madison.bahmer@istresearch.com>


# copy crawler own requirements.txt with its dependencies
COPY crawler/requirements.txt /usr/src/app/

# Combine run command to create single intermeiate image layer
# This MANDATORY because developments dependencies are huge.
RUN mkdir -p /usr/src/app \
 && cd /usr/src/app \
# Installing runtime dependencies
 && apk --no-cache add \
      curl \
      openssl \
      libffi \
      libxml2 \
      libxslt \
# Installing buildtime dependencies. They will be removed at end of this
# commands sequence.
 && apk --no-cache add --virtual build-dependencies \
      build-base \
      openssl-dev \
      libffi-dev \
      libxml2-dev \
      libxslt-dev \
# Updating pip itself before installing packages from requirements.txt
 && pip install --no-cache-dir pip setuptools \
# Installing pip packages from requirements.txt
 && pip install --no-cache-dir -r requirements.txt \
# Removing build dependencies leaving image layer clean and neat
 && apk del build-dependencies

# move codebase over
COPY crawler /usr/src/app

WORKDIR /usr/src/app

# override settings via localsettings.py
COPY docker/crawler/settings.py /usr/src/app/crawling/localsettings.py

# copy testing script into container
COPY docker/run_docker_tests.sh /usr/src/app/run_docker_tests.sh

# set up environment variables

# run command
CMD ["scrapy", "runspider", "crawling/spiders/link_spider.py"]
