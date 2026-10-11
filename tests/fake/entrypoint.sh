#!/bin/sh
# Create a hosts file, like a freshly booted virtual machine. The
# container is run with --no-hosts, so the hosts file is a regular file
# which can be updated by the prepare playbook.
cat > /etc/hosts <<HOSTS
127.0.0.1	localhost
127.0.1.1	$(hostname)
::1	localhost ip6-localhost ip6-loopback
HOSTS
chmod 0644 /etc/hosts
exec sleep infinity
