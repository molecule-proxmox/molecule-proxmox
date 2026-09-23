Options
=======

The molecule-proxmox driver is configured with a ``driver.options`` block in
your ``molecule.yml``, plus per-instance overrides under ``platforms:``. See
:doc:`examples` for complete configuration examples.

Connection options
-------------------

``api_host``
  Proxmox API host name or address. Required.

``api_port``
  Proxmox API port. Optional; the standard Proxmox port (8006) is used
  when omitted.

``api_user``
  Proxmox API user, in ``user@realm`` form (e.g. ``root@pam``). Required.

``api_password``
  Proxmox API password. Either ``api_password`` or both ``api_token_id``
  and ``api_token_secret`` must be set.

``api_token_id`` / ``api_token_secret``
  Proxmox API token, used instead of ``api_password``. Both must be set
  together.

``api_timeout``
  Time limit, in seconds, for requests to the Proxmox API. Optional;
  defaults to 5 seconds when omitted.

``validate_certs``
  Whether to validate the Proxmox API's TLS certificate. Optional;
  defaults to ``true``. Set to ``false`` for a self-signed certificate.

``node``
  Proxmox node name to create instances on. Required.

Instance options
------------------

``ssh_user``
  SSH user for connecting to created instances. Optional; defaults to
  ``molecule``.

``ssh_port``
  SSH port for connecting to created instances. Optional; defaults to
  ``22``.

``ssh_identity_file``
  Path to the SSH private key file for connecting to created instances.
  Required.

``template_name``
  Default Proxmox template to clone when a platform does not specify its
  own. See `Platform options`_ for the full template-selection precedence.

``full``
  Whether to create a full clone instead of a linked clone. Optional; if
  omitted, this is left to ``community.proxmox.proxmox_kvm``'s own default,
  which creates a full clone for a regular VM but a linked clone when
  cloning from a VM template.

``timeout``
  Timeout, in seconds, used for two separate things: how long to wait for
  the Proxmox API clone/destroy operation to complete (30 seconds if
  omitted), and how long to wait for the QEMU guest agent to report an IP
  address after starting the instance (300 seconds if omitted). Setting
  this option overrides both with the same value.

``pool``
  Proxmox resource pool to add created instances to. Optional; no pool is
  set when omitted.

``sethostname``
  Whether to set the instance's hostname (and fix up ``/etc/hosts``) after
  cloning. Optional; defaults to ``true``. Set to ``false`` to leave the
  cloned template's hostname untouched.

``debug``
  Enable verbose logging of the ``proxmox_secrets`` tasks, for
  troubleshooting. Optional; defaults to ``false``.

``proxmox_secrets``
  Path to a file or executable that provides any of the connection options
  above, so they don't need to be stored directly in ``molecule.yml``. See
  :doc:`examples`.

Platform options
------------------

These are set per-instance, under ``platforms:`` in ``molecule.yml``,
alongside each instance's ``name``.

``name``
  Instance name. Required.

``template_name`` / ``proxmox_template_name``
  Proxmox template to clone for this instance. ``proxmox_template_name``
  takes precedence if both are set. Falls back to the driver-level
  ``template_name`` option, then to ``box``, then to the literal
  ``molecule`` if none are set.

``template_vmid`` / ``proxmox_template_vmid``
  Clone this instance from a template identified by vmid instead of name.
  ``proxmox_template_vmid`` takes precedence if both are set.

``newid``
  vmid to assign to the cloned instance. Optional; Proxmox assigns the
  next available vmid when omitted.

``box``
  Alternate fallback for the template name, for compatibility with
  ``molecule.yml`` files migrated from other drivers. Lowest precedence in
  the template-selection chain; see ``template_name`` above.

``ciuser``, ``cipassword``, ``citype``, ``ipconfig``, ``nameservers``, ``searchdomains``, ``sshkeys``
  cloud-init settings, applied only if the cloned template has a
  cloud-init drive. See the `proxmox_kvm`_ module documentation for value
  formats.

.. _`proxmox_kvm`: https://docs.ansible.com/projects/ansible/latest/collections/community/proxmox/proxmox_kvm_module.html
