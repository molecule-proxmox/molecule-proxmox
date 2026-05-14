***********************
Molecule Proxmox Plugin
***********************

This is an Ansible Molecule Driver plugin to manage instances on a
`Proxmox VE`_ hypervisor cluster.  Only virtual machines are supported at this
time.

Requirements
============

* Access to a `Proxmox VE`_ cluster
* One or more virtual machine templates with required setup
* Python package `proxmoxer`_
* Ansible module `community.general.proxmox_kvm`_

The required Python packages are automatically installed when
``molecule-proxmox`` is installed with ``pip``.

The ``proxmox_kvm`` module is included with the Community.General collection
and is automatically installed when Ansible is installed with ``pip``.

If you choose to run a newer version of the ``community.general`` collection,
be aware that Molecule Proxmox is not compatible with ``community.general``
version >=10.7.0 due ``proxmox_kvm`` being moved to its own
collection, ``community.proxmox``. These changes which will probably be
picked up in Ansible 12 and, at that point, in Molecule Proxmox as well.

Virtual machine template requirements
-------------------------------------

The molecule instances are created by cloning Proxmox virtual machine
templates.  You will need to create one or more templates.

Templates have the following requirements.

* A cloud-init drive if any cloud-init settings are used
* networking configured
* Python installed for Ansible
* qemu-guest-agent installed and enabled in Proxmox
* ssh server installed
* user account for Ansible
* An ssh public key must be added to the ``authorized_keys`` for the Ansible user account.
* If a non-root user is used for the Ansible user (recommended), that user should be
  added to the sudoers. (This is not needed for the driver, but will likely be needed
  for the ``converge`` playbook.)

Installation
============

The ``molecule-proxmox`` plugin may be installed with Python ``pip``. A virtualenv
is recommended.  The following commands install Ansible, Molecule, and the
Molecule Proxmox plugin in a virtualenv called ``venv``.

.. code-block:: bash

    $ python3 -m venv venv
    $ . venv/bin/activate
    $ pip3 install ansible-core molecule molecule-proxmox

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
settings for the proxmox API connection, such as api_password. If this is a regular
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
       # See https://docs.ansible.com/ansible/latest/collections/community/general/proxmox_kvm_module.html
       # for cloud-init options.
       ciuser: some_user
       cipassword: some_password
       ipconfig:
         ipconfig0: 'ip=192.168.0.2/24,gw=192.168.0.1'
       nameservers:
         - 192.169.0.245

Development
===========

To checkout the source code:

.. code-block:: bash

    git clone https://github.com/meffie/molecule-proxmox
    cd molecule-proxmox

Install `tox` with `pipx`, your system package manager, or create
a virtualenv.

.. code-block:: bash

    pipx install tox

Copy the `envrc.sample` file to `.envrc` and edit the `.envrc` for your local
proxmox site. Source the `.envrc` file to to export the environment variables
to the current shell.

To run the tests with the latest supported molucule version:

.. code-block:: bash

    tox -e latest

To list the tox test environments

.. code-block:: bash

    tox list

To run tests with other versions:

.. code-block:: bash

    tox -e <testenv> -- [<pytest_options>]


Authors
=======

Molecule Proxmox Plugin was created by Michael Meffie based on code from
Molecule.

License
=======

The `MIT`_ License.


.. _`Proxmox VE`: https://www.proxmox.com/en/proxmox-ve
.. _`proxmoxer`: https://pypi.org/project/proxmoxer/
.. _`community.general.proxmox_kvm`: https://docs.ansible.com/ansible/11/collections/community/general/proxmox_kvm_module.html
.. _`MIT`: https://github.com/meffie/molecule-proxmox/blob/master/LICENSE
