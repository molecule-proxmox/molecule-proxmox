Development
===========

To checkout the source code:

.. code-block:: bash

    git clone https://github.com/molecule-proxmox/molecule-proxmox
    cd molecule-proxmox

Install ``tox`` with ``pipx``, your system package manager, or create
a virtualenv.

.. code-block:: bash

    pipx install tox

Copy the ``envrc.sample`` file to ``.envrc`` and edit the ``.envrc`` for your local
proxmox site. Source the ``.envrc`` file to export the environment variables
to the current shell.

To run the tests with the latest supported molecule version:

.. code-block:: bash

    tox -e latest

To list the tox test environments:

.. code-block:: bash

    tox list

To run tests with other versions:

.. code-block:: bash

    tox -e <testenv> -- [<pytest_options>]

Testing without a Proxmox cluster
---------------------------------

The tests can be run with a fake Proxmox server instead of a real Proxmox
cluster, with the ``--fake`` pytest option. This requires ``podman``, but
no ``.envrc`` settings:

.. code-block:: bash

    tox -e latest -- --fake

The fake Proxmox API server runs in the pytest process, with an in-memory
cluster of two nodes, each with a local copy of a template with the same
name. The fake virtual machines are ``podman`` containers, built from
``tests/fake/Containerfile``, so the complete ``molecule test`` sequence is
run, including ``prepare`` and ``converge``. The ``--fake`` option may be
used with any of the tox test environments, to test the driver with all of
the supported Ansible and Molecule versions:

.. code-block:: bash

    tox -- --fake

.. note::

   Do not run the tox test environments in parallel (``tox p``) with the
   ``--fake`` option. Each test environment starts its own fake Proxmox
   server, and the fake virtual machines of the test environments would
   have the same addresses and container names. For the same reason, the
   tests can not be run in parallel with ``pytest-xdist``.

The fake Proxmox server implements only the part of the Proxmox API used
by the driver, so the tests should still be run with a real Proxmox
cluster before a release.

The multiple node test and the unmanaged instance test are skipped with a
real Proxmox cluster, unless ``TEST_PROXMOX_NODE2`` and
``TEST_PROXMOX_UNMANAGED_ADDRESS`` are set in the ``.envrc`` file.
