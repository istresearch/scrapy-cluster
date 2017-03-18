#!/bin/bash

set -e

# Build proivisioning container
sudo docker pull ${distribution}:${version}
sudo docker build --rm=true --file=docker/travisci/Dockerfile.${distribution}-${version} --tag=${distribution}-${version}:ansible docker
container_id=$(mktemp)

# Run container in detached state
sudo docker run --detach --volume="${PWD}":"${PWD}":rw ${run_opts} ${distribution}-${version}:ansible "${init}" > "${container_id}"

# Ansible syntax check.
sudo docker exec --tty "$(cat ${container_id})" env TERM=xterm /bin/bash -c "ansible-playbook -i ${PWD}/ansible/travis.inventory ${PWD}/ansible/scrapy-cluster.yml --syntax-check"

# Ansible install playbook.
sudo docker exec --tty "$(cat ${container_id})" env TERM=xterm /bin/bash -c "ansible-playbook -i ${PWD}/ansible/travis.inventory ${PWD}/ansible/scrapy-cluster.yml --connection=local --become"

# Install coveralls and other pip requiremnts
sudo docker exec --tty "$(cat ${container_id})" env TERM=xterm /bin/bash -c "virtualenv ${PWD}/sc; source ${PWD}/sc/bin/activate; pip install -r ${PWD}/requirements.txt; cd ${PWD}; find . -name "*.pyc" -type f -delete;"

# Run offline tests
sudo docker exec --tty "$(cat ${container_id})" env TERM=xterm /bin/bash -c "source ${PWD}/sc/bin/activate; cd ${PWD}; ./run_offline_tests.sh"

# Run online tests
sudo docker exec --tty "$(cat ${container_id})" env TERM=xterm /bin/bash -c "source ${PWD}/sc/bin/activate; cd ${PWD}; ./run_online_tests.sh"

# Stop Docker Ansible Containers
sudo docker stop "$(cat ${container_id})"

# send coverage report
pip install coveralls; coveralls