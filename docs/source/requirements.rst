Requirements
============

* Molecule
* Ansible (``ansible`` or ``ansible-core`` packages)
* Ansible ``community.proxmox`` collection
* Python package `proxmoxer`_
* Access to a `Proxmox VE`_ cluster
* One or more virtual machine templates with required setup

The required Python packages are automatically installed when
``molecule-proxmox`` is installed with ``pip``.

The `community.proxmox`_ collection is bundled with the ``ansible`` package,
but not with ``ansible-core`` package. The ``community.proxmox`` collection can
be installed with::

    ansible-galaxy collection install community.proxmox

Alternately, you can have Molecule install it for you automatically by adding
a Galaxy dependency to your scenario's ``molecule.yml``, along with a
``collections.yml`` file next to it:

.. code-block:: yaml

   # molecule.yml
   dependency:
     name: galaxy

.. code-block:: yaml

   # collections.yml
   collections:
     - name: community.proxmox

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

.. _`Proxmox VE`: https://www.proxmox.com/en/proxmox-ve
.. _`proxmoxer`: https://pypi.org/project/proxmoxer/
.. _`community.proxmox`: https://docs.ansible.com/projects/ansible/latest/collections/community/proxmox/
