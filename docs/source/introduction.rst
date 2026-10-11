Introduction
============

``molecule-proxmox`` is an Ansible `Molecule`_ driver plugin which creates
the Molecule test instances as virtual machines on a `Proxmox VE`_
hypervisor cluster. This lets you test Ansible roles and playbooks with
Molecule on full virtual machines, built from the same templates you use
for your other Proxmox virtual machines.

Only virtual machines are supported at this time; containers (LXC) are not.

How it works
------------

``molecule create``
  Clones each instance from a Proxmox virtual machine template, applies
  any cloud-init settings, and starts the instance. The driver waits for
  the QEMU guest agent to report the IP address of the instance, then
  saves the address so Molecule can connect to the instance with SSH.

``molecule prepare``
  Waits for the SSH connection to the instance, and by default sets the
  host name of the instance to the instance name.

``molecule destroy``
  Stops and removes the instances created by the driver. In snapshot
  mode, the instances are kept and rolled back to a snapshot instead, so
  the next create is fast.

Features
--------

* Clone instances from templates by name or by vmid, as full or linked
  clones.
* Create instances on different nodes of a Proxmox cluster.
* Configure the cloned instances with cloud-init settings.
* Add the instances to a Proxmox resource pool.
* Authenticate with a password or an API token, and load the credentials
  from a file or a script instead of storing them in ``molecule.yml``.
* Use existing machines as *unmanaged* instances, alongside the cloned
  instances.
* Keep the instances between test runs, and reset them to a snapshot on
  destroy, instead of cloning them again for every run. See
  :doc:`snapshots`.

See :doc:`requirements` to get started.

.. _`Molecule`: https://ansible.readthedocs.io/projects/molecule/
.. _`Proxmox VE`: https://www.proxmox.com/en/proxmox-ve
