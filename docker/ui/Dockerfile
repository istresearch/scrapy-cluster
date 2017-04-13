FROM python:2.7
MAINTAINER Madison Bahmer <madison.bahmer@istresearch.com>

# os setup
RUN apt-get update
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# install requirements
COPY ui/requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# move codebase over
COPY ui /usr/src/app

# override settings via localsettings.py
COPY docker/ui/settings.py /usr/src/app/localsettings.py

# copy testing script into container
# Unknown tests yet
#COPY docker/run_docker_tests.sh /usr/src/app/run_docker_tests.sh

# set up environment variables

# run command
CMD ["python", "ui_service.py"]