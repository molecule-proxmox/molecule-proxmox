Snapshot mode
=============

By default, ``molecule destroy`` removes the instances, and the next
``molecule create`` clones them again from the template. Cloning, and
especially a full clone, can take a while, which slows down a test
workflow that destroys and creates the instances many times.

In snapshot mode, the driver keeps the instances instead. The first
create clones each instance and takes a snapshot of it, and destroy rolls
the instance back to that snapshot. The next create starts the instance
from the snapshot, which is much faster than cloning, and the instance is
in the same clean state as a newly cloned one.

Enabling snapshot mode
----------------------

Set the ``snapshot`` driver option. We recommend setting it from an
environment variable, so the kept instances can be removed later (see
`Removing the kept instances`_):

.. code-block:: yaml

   driver:
     name: molecule-proxmox
     options:
        api_host: <hostname>
        api_user: <name>@<realm>
        api_password: "********"
        node: pve01
        ssh_user: tester
        ssh_identity_file: /path/to/id_rsa
        template_name: debian11
        snapshot: "${MOLECULE_PROXMOX_SNAPSHOT:-true}"
   platforms:
     - name: test01
     - name: test02

The snapshot is named ``molecule`` by default. Set the ``snapshot_name``
option to use a different name.

How it works
------------

``molecule create``
  For each instance without a kept VM, the driver clones the template,
  applies the cloud-init settings, and takes a snapshot of the VM before
  it is first started. For each instance with a kept VM, the driver stops
  the VM and rolls it back to the snapshot, in case the previous run was
  interrupted before destroy. Then all of the instances are started, as
  usual.

``molecule prepare``
  Runs as usual. Since the snapshot is taken before the first boot, the
  instance boots fresh on every create, and prepare sets the host name
  every time.

``molecule destroy``
  Stops the kept VMs and rolls them back to the snapshot. All changes
  made since the snapshot, for example by converge, are discarded. The
  VMs are not removed.

``molecule test``
  Runs destroy at the start and the end of the test sequence, as usual,
  so each test starts from the snapshot and leaves the VMs rolled back.

The vmids of the kept VMs are saved in the file ``proxmox_snapshot.yml``
in the molecule ephemeral directory of the scenario. The ephemeral
directory is separate for each user, project directory, and scenario, so
two people running the same scenario on the same Proxmox cluster each get
their own kept VMs. Before using a saved vmid, the driver checks that the
VM still exists with the instance name. If it does not, for example
because the VM was removed in the Proxmox web interface, the driver
forgets the saved vmid and clones a new VM.

Removing the kept instances
---------------------------

To remove the kept VMs, run destroy with snapshot mode turned off. With
the configuration shown above:

.. code-block:: console

   $ MOLECULE_PROXMOX_SNAPSHOT=false molecule destroy

This removes the kept VMs and the saved vmids. The next create clones new
VMs.

Remove the kept VMs when:

* The template has been updated. The kept VMs were cloned from the old
  template, and are not updated.

* The platform settings used when cloning have changed, for example the
  template name, node, ``newid``, or the cloud-init settings. These
  settings are captured in the snapshot, and are not applied again to a
  kept VM.

* A platform has been removed from ``molecule.yml``. Its kept VM is
  still saved, and is only removed with the other kept VMs.

* You are done testing, and want to free the resources used by the kept
  VMs on the Proxmox cluster.

.. warning::

   ``molecule reset`` removes the ephemeral directory, including the
   saved vmids. Run destroy with snapshot mode turned off before running
   ``molecule reset``. Otherwise, the driver no longer knows about the
   kept VMs, and the next create clones new VMs. The old VMs are left on
   the Proxmox cluster and must be removed manually.

   To find the kept VMs before a reset, look at the saved vmids in the
   ephemeral directory of the scenario. By default, the ephemeral
   directory is under ``~/.ansible/tmp``, unless
   ``MOLECULE_EPHEMERAL_DIRECTORY`` is set:

   .. code-block:: console

      $ cat ~/.ansible/tmp/molecule.*.<scenario>/proxmox_snapshot.yml
      instances:
          test01: 101
          test02: 102

Proxmox permissions
-------------------

In addition to the permissions needed to clone, start, and remove VMs,
the Proxmox user (or API token) needs permission to take and roll back
snapshots: ``VM.Snapshot`` and ``VM.Snapshot.Rollback``.

Interaction with other options
------------------------------

* Unmanaged instances (instances with an ``address``) are never cloned,
  snapshotted, or removed, with or without snapshot mode.

* Linked clones (``full: false``) and full clones may both be used with
  snapshot mode.

* Instances created before snapshot mode was turned on are removed by
  destroy as usual. The next create clones new instances and keeps them.
