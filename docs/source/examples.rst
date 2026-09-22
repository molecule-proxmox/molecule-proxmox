Examples
========

.. code-block:: yaml

   driver:
     name: molecule-proxmox
     options:
        api_host: <hostname>        # e.g. pve01.example.com
        api_user: <name>@<realm>    # e.g. root@pam
        api_password: "********"
        node: pve01
        ssh_user: tester
        ssh_port: 22022             # default to 22
        ssh_identity_file: /path/to/id_rsa
   platforms:
     - name: test01
       template_name: debian11
     - name: test02
       template_name: alma8

.. code-block:: yaml

   driver:
     name: molecule-proxmox
     options:
        api_host: <hostname>        # e.g. pve01.example.com
        api_port: 18006             # custom proxmox port number
        api_user: <name>@<realm>    # e.g. root@pam
        # Optional: Use an API token for Proxmox authentication.
        api_token_id: "********"
        api_token_secret: "*******************************"
        api_timeout: 10
        # Disable TLS validation for self-signed certs.
        validate_certs: false
        node: pve01
        ssh_user: tester
        ssh_port: 22022             # default to 22
        ssh_identity_file: /path/to/id_rsa
        # Optional: The default template name.
        template_name: debian11
        # Optional: Set the hostname after cloning.
        sethostname: yes
        # Optional: Create the VMs in the pool.
        pool: test
        # Optional: Create Linked clone instead of Full clone.
        full: false
   platforms:
     - name: test01
       # Optional: Specify the VM id of the clone.
       newid: 216
     - name: test02
       # Optional: Specify the VM id of the clone.
       newid: 217

.. code-block:: yaml

   driver:
     name: molecule-proxmox
     options:
        proxmox_secrets: /path/to/proxmox_secrets.yml
        node: pve01
        ssh_user: tester
        ssh_port: 22022             # default to 22
        ssh_identity_file: /path/to/id_rsa
        template_name: debian11
   platforms:
     - name: test01
     - name: test02

The ``proxmox_secrets`` setting specifies the path to an external file with
settings for the Proxmox API connection, such as api_password. If this is a regular
file, it should be a yaml file with the settings to be included. If the file is
an executable, the file will be run and the stdout will be combined with the
driver options. The output of the script needs to be valid yaml
consisting of dictionary keys and values (e.g. ``api_password: foobar``).

The value of ``proxmox_secrets`` will be passed into ``ansible.builtin.cmd``.
Therefore, any additional argument values will be passed to the script as well.

This allows you to use an external password manager to store
the Proxmox API connection settings.  For example with a script:

.. code-block:: yaml

   driver:
     name: molecule-proxmox
     options:
        debug: true  # Enable logging proxmox_secrets tasks for troubleshooting
        proxmox_secrets: /usr/local/bin/proxmox_secrets.sh
        node: pve01

.. code-block:: bash

    $ cat /usr/local/bin/proxmox_secrets.sh
    #!/bin/sh
    pass proxmox/pve01

Or with a file (which **must** not be executable):

.. code-block:: yaml

   driver:
     name: molecule-proxmox
     options:
        debug: true  # Enable logging proxmox_secrets tasks for troubleshooting
        proxmox_secrets: $HOME/proxmox_secrets.yaml
        node: pve01

.. code-block:: yaml

    $ cat $HOME/proxmox_secrets.yaml
    ---
    api_host: my-proxmox-host
    api_user: my-proxmox-user@pam
    api_password: my-secret-password

Finally, a configuration example with many features enabled:

.. code-block:: yaml

   driver:
     name: molecule-proxmox
     options:
        proxmox_secrets: /path/to/proxmox_secrets.yml
        node: pve01
        ssh_user: tester
        ssh_port: 22022             # default to 22
        ssh_identity_file: /path/to/id_rsa
        template_name: debian11
   platforms:
     - name: test01
       newid: 1000
       template_name: debian11
       # See proxmox_kvm module documentation for cloud-init options.
       ciuser: some_user
       cipassword: some_password
       ipconfig:
         ipconfig0: 'ip=192.168.0.2/24,gw=192.168.0.1'
       nameservers:
         - 192.169.0.245
