Installation
============

Install ``molecule-proxmox`` with Python ``pip`` or ``uv``. A virtualenv is
recommended, though not required -- for example, one may not be needed
when installing inside a container. The following commands create a
virtualenv named ``venv`` and install Ansible, Molecule, and
``molecule-proxmox`` into it.

.. code-block:: bash

    $ python3 -m venv venv
    $ . venv/bin/activate
    $ pip3 install ansible-core molecule molecule-proxmox

Alternately, if you use `uv`_:

.. code-block:: bash

    $ uv venv venv
    $ . venv/bin/activate
    $ uv pip install ansible-core molecule molecule-proxmox

Proxmox collection
-------------------

molecule-proxmox uses the Ansible `community.proxmox`_ collection to talk to
the Proxmox API. This collection is bundled with the ``ansible`` package,
but not with the ``ansible-core`` package. If you installed ``ansible-core``
above, install the collection separately::

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

.. _`community.proxmox`: https://docs.ansible.com/projects/ansible/latest/collections/community/proxmox/
.. _`uv`: https://docs.astral.sh/uv/
