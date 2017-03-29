FROM python:2.7.12-alpine
MAINTAINER Madison Bahmer <madison.bahmer@istresearch.com>

# copy rest own requirements.txt with its dependencies
COPY rest/requirements.txt /usr/src/app/

# Combine run command to create single intermeiate image layer
# This MANDATORY because developments dependencies are huge.
RUN mkdir -p /usr/src/app \
 && cd /usr/src/app \
# Installing runtime dependencies
 && apk --no-cache add \
      curl \
# Installing buildtime dependencies. They will be removed at end of this
# commands sequence.
 && apk --no-cache add --virtual build-dependencies \
      build-base \
# Updating pip itself before installing packages from requirements.txt
 && pip install --no-cache-dir pip setuptools \
# Installing pip packages from requirements.txt
 && pip install --no-cache-dir -r requirements.txt \
# Removing build dependencies leaving image layer clean and neat
 && apk del build-dependencies

# move codebase over
COPY rest /usr/src/app

WORKDIR /usr/src/app

# override settings via localsettings.py
COPY docker/rest/settings.py /usr/src/app/localsettings.py

# copy testing script into container
COPY docker/run_docker_tests.sh /usr/src/app/run_docker_tests.sh

# set up environment variables

# run command
CMD ["python", "rest_service.py"]
