lint:
	pylint --rcfile .pylintrc --recursive=y .
	yamllint .
	ANSIBLE_LIBRARY=src/molecule_proxmox/modules ansible-lint -c .ansible-lint.yml
