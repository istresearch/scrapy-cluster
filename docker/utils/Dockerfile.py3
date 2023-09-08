FROM python:3.10
MAINTAINER Madison Bahmer <madison.bahmer@istresearch.com>

# os setup
RUN apt-get update && apt-get -y install iputils-ping
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# move codebase over and install requirements
COPY utils /usr/src/app
RUN pip install .
RUN pip install nose2

# copy testing script into container
COPY docker/run_docker_tests.sh /usr/src/app/run_docker_tests.sh

# set up environment variables

# run command
CMD ["ping", "localhost"]