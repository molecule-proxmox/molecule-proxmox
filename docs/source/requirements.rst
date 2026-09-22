Requirements
============

* Molecule 25.12 or later
* Ansible
* Ansible ``community.proxmox`` collection
* Python package `proxmoxer`_
* API credentials for a `Proxmox VE`_ cluster, with permission to clone,
  start, and delete virtual machines
* One or more virtual machine templates, prepared as described in
  `Virtual machine template requirements`_

Virtual machine template requirements
-------------------------------------

The molecule instances are created by cloning Proxmox virtual machine
templates.  You will need to create one or more templates.

Templates have the following requirements.

* Cloud-init drive attached, if cloud-init settings are used
* Networking configured
* Python installed for Ansible
* ``qemu-guest-agent`` installed and enabled in Proxmox
* SSH server installed
* Ansible user account created
* Ansible user's SSH public key added to ``authorized_keys``
* Non-root Ansible user (recommended) added to ``sudoers`` -- not required by
  the driver itself, but likely needed by the ``converge`` playbook

.. _`Proxmox VE`: https://www.proxmox.com/en/proxmox-ve
.. _`proxmoxer`: https://pypi.org/project/proxmoxer/
