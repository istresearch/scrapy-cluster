# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.7.4"

Vagrant.configure(2) do |config|

  # Configure general VM options
  config.vm.provider "virtualbox" do |vb|
    vb.memory = 2048
    vb.cpus = 4
  end

  config.vm.define 'scdev' do |node|
    node.vm.box = 'ubuntu/trusty64'
    node.vm.hostname = 'scdev'
    node.vm.network "private_network", ip: "192.168.33.99"
    node.vm.provision "ansible" do |ansible|
      ansible.verbose = true
      ansible.groups = {
        "kafka" => ["scdev"],
        "zookeeper" => ["scdev"],
        "redis" => ["scdev"],
        "virtualenv" => ["scdev"],
        "all_groups:children" => ["kafka", "zookeeper", "redis", "virtualenv"]
      }
      ansible.playbook = "ansible/scrapy-cluster.yml"
    node.vm.provision "shell", inline: "service supervisord restart", run: "always"
    end
  end
end
