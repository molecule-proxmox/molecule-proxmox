#  Copyright (c) 2022 Sine Nomine Associates
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to
#  deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#  FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#  DEALINGS IN THE SOFTWARE.

import os

from molecule import logger
from molecule import util
from molecule.api import Driver


LOG = logger.get_logger(__name__)


class Proxmox(Driver):
    """
    The class responsible for managing instances with Proxmox.

    .. code-block:: yaml

        driver:
          name: proxmox
        platforms:
          - name: instance
            template: generic-centos-8
            memory: 1024
            cpus: 1

    .. code-block:: bash

        $ pip install molecule-proxmox

    """  # noqa

    def __init__(self, config=None):
        super(Proxmox, self).__init__(config)
        self._name = "molecule-proxmox"
        library_path = os.environ.get("ANSIBLE_LIBRARY", "")
        if library_path:
            library_path = self.modules_dir() + ":" + library_path
        else:
            library_path = self.modules_dir()
        os.environ["ANSIBLE_LIBRARY"] = library_path

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def login_cmd_template(self):
        connection_options = " ".join(self.ssh_connection_options)
        return (
            "ssh {{address}} "
            "-l {{user}} "
            "-p {{port}} "
            "-i {{identity_file}} "
            "{}"
        ).format(connection_options)

    @property
    def default_safe_files(self):
        return []

    @property
    def default_ssh_connection_options(self):
        return self._get_ssh_connection_options()

    def login_options(self, instance_name):
        d = {"instance": instance_name}
        return util.merge_dicts(d, self._get_instance_config(instance_name))

    def ansible_connection_options(self, instance_name):
        try:
            d = self._get_instance_config(instance_name)
            return {
                "ansible_user": d["user"],
                "ansible_host": d["address"],
                "ansible_port": d["port"],
                "ansible_private_key_file": d["identity_file"],
                "ansible_connection": "ssh",
                "ansible_ssh_common_args": " ".join(self.ssh_connection_options),  # noqa: E501
            }
        except StopIteration:
            return {}
        except IOError:
            # Instance has yet to be provisioned, therefore the
            # instance_config is not on disk.
            return {}

    def _get_instance_config(self, instance_name):
        instance_config_dict = util.safe_load_file(self._config.driver.instance_config)  # noqa: E501
        return next(
            item for item in instance_config_dict if item["instance"] == instance_name   # noqa: E501
        )

    def sanity_checks(self):
        pass

    def template_dir(self):
        """Return path to its own cookiecutterm templates. It is used by init
        command in order to figure out where to load the templates from.
        """
        return os.path.join(os.path.dirname(__file__), "cookiecutter")

    def modules_dir(self):
        return os.path.join(os.path.dirname(__file__), "modules")

    def schema_file(self):
        return os.path.join(os.path.dirname(__file__), "driver.json")
