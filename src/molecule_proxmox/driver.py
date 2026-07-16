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

from molecule import logger, util
from molecule.api import Driver

LOG = logger.get_logger(__name__)


class Proxmox(Driver):
    def __init__(self, config=None):
        super().__init__(config)
        self._name = "molecule-proxmox"
        # We removed the global os.environ manipulation from here.

    @property
    def env(self):
        """Environment variables for the driver."""
        env_dict = os.environ.copy()
        library_path = self.modules_dir()

        # Merge our custom modules path with any existing ANSIBLE_LIBRARY paths
        existing_library = env_dict.get("ANSIBLE_LIBRARY", "")
        if existing_library:
            env_dict["ANSIBLE_LIBRARY"] = f"{library_path}:{existing_library}"
        else:
            env_dict["ANSIBLE_LIBRARY"] = library_path

        return env_dict

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def login_cmd_template(self):
        connection_options = " ".join(self.ssh_connection_options)
        return f"ssh {{address}} -l {{user}} -p {{port}} -i {{identity_file}} {connection_options}"

    @property
    def default_safe_files(self):
        return []

    @property
    def default_ssh_connection_options(self):
        return self._get_ssh_connection_options()

    def login_options(self, instance_name):
        return util.merge_dicts({"instance": instance_name}, self._get_instance_config(instance_name))

    def ansible_connection_options(self, instance_name):
        try:
            config_dict = self._get_instance_config(instance_name)
            return {
                "ansible_user": config_dict["user"],
                "ansible_host": config_dict["address"],
                "ansible_port": config_dict["port"],
                "ansible_private_key_file": config_dict["identity_file"],
                "connection": "ssh",
                "ansible_ssh_common_args": " ".join(self.ssh_connection_options),
            }
        except (StopIteration, IOError):
            return {}

    def _get_instance_config(self, instance_name):
        instance_config_dict = util.safe_load_file(self._config.driver.instance_config)
        return next(item for item in instance_config_dict if item["instance"] == instance_name)

    def sanity_checks(self):
        pass

    def template_dir(self):
        return os.path.join(os.path.dirname(__file__), "cookiecutter")

    def modules_dir(self):
        return os.path.join(os.path.dirname(__file__), "modules")
