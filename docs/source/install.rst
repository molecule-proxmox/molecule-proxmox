Installation
============

The ``molecule-proxmox`` plugin may be installed with Python ``pip``. A virtualenv
is recommended.  The following commands install Ansible, Molecule, and the
Molecule Proxmox plugin in a virtualenv called ``venv``.

.. code-block:: bash

    $ python3 -m venv venv
    $ . venv/bin/activate
    $ pip3 install ansible-core molecule molecule-proxmox
