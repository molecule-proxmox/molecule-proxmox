Development
===========

To checkout the source code:

.. code-block:: bash

    git clone https://github.com/molecule-proxmox/molecule-proxmox
    cd molecule-proxmox

Install `tox` with `pipx`, your system package manager, or create
a virtualenv.

.. code-block:: bash

    pipx install tox

Copy the `envrc.sample` file to `.envrc` and edit the `.envrc` for your local
proxmox site. Source the `.envrc` file to to export the environment variables
to the current shell.

To run the tests with the latest supported molecule version:

.. code-block:: bash

    tox -e latest

To list the tox test environments

.. code-block:: bash

    tox list

To run tests with other versions:

.. code-block:: bash

    tox -e <testenv> -- [<pytest_options>]
