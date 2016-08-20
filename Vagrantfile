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
    # node.vm.box = 'centos/7'
    node.vm.hostname = 'scdev'
    node.vm.network "private_network", ip: "192.168.33.99"
    node.vm.provision "ansible_local" do |ansible|
      ansible.playbook = "ansible/scrapy-cluster.yml"
      ansible.inventory_path = "ansible/sc.inventory"
      ansible.raw_arguments = ["-c", "local"]
    end
    node.vm.provision "shell", inline: "service supervisord restart", run: "always"
  end
end
