#!/bin/bash
wget -O /tmp/puppet-release.deb http://apt.puppetlabs.com/puppetlabs-release-pc1-xenial.deb &&\
    dpkg -i /tmp/puppet-release.deb &&\
    apt-get -q update &&\
    export DEBIAN_FRONTEND=noninteractive ;\
    apt-get -q -y dist-upgrade -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" --force-yes &&\
    apt-get -q -y --force-yes install puppet-agent &&\
    apt-get -q clean &&\
    apt-get -q -y --purge autoremove &&\
    augtool -s set /files/etc/default/puppet/START yes
rm -f /tmp/puppet-release.deb
