#!/usr/bin/python

import time
import syslog

from ansible.module_utils.basic import AnsibleModule
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

def get_vm(module, proxmox, vmid):
    vm_list = [vm for vm in proxmox.cluster.resources.get(type="vm") if vm["vmid"] == int(vmid)]
    if len(vm_list) == 0:
        module.fail_json(vmid=vmid, msg=f"VM with vmid = {vmid} not found")
    if len(vm_list) > 1:
        module.fail_json(vmid=vmid, msg=f"Multiple VMs with vmid = {vmid} found")
    return vm_list[0]


def start_vm(module, proxmox, vm):
    vmid = vm["vmid"]
    proxmox_node = proxmox.nodes(vm["node"])
    timeout = module.params["timeout"]

    syslog.syslog(f"Starting vmid {vmid}")
    taskid = proxmox_node.qemu(vm["vmid"]).status.start.post()

    while timeout:
        task = proxmox_node.tasks(taskid).status.get()
        if task["status"] == "stopped" and task["exitstatus"] == "OK":
            time.sleep(1)
            return
        timeout -= 1
        if timeout == 0:
            break
        time.sleep(1)

    lastlog = proxmox_node.tasks(taskid).log.get()[:1]
    msg = f"Timeout while starting vmid {vmid}: {lastlog}"
    syslog.syslog(msg)
    module.fail_json(msg=msg)


def query_vm(module, proxmox, vm):
    vmid = vm["vmid"]
    proxmox_node = proxmox.nodes(vm["node"])
    timeout = module.params["timeout"]

    syslog.syslog(f"Waiting for vmid {vmid} IP address")

    while timeout:
        reply = None
        try:
            reply = proxmox_node.qemu(vmid).agent.get("network-get-interfaces")
        except ResourceException as err:
            if err.status_code == 500 and f"VM {vmid} is not running" in err.content:
                start_vm(module, proxmox, vm)
            elif err.status_code == 500 and "QEMU guest agent is not running" in err.content:
                pass
            else:
                module.fail_json(msg=str(err))

        if reply and "result" in reply:
            addresses = i2a(reply["result"])
            if len(addresses) > 0:
                return addresses

        timeout -= 1
        if timeout == 0:
            break
        time.sleep(1)

    msg = f"Timeout while waiting for vmid {vmid} IP address"
    syslog.syslog(msg)
    module.fail_json(msg=msg)
    return None


def i2a(interfaces):
    addrs = []
    for interface in interfaces:
        if "ip-addresses" in interface:
            for ip_address in interface["ip-addresses"]:
                atype = ip_address.get("ip-address-type", "")
                aip = ip_address.get("ip-address", "")
                if aip and atype == "ipv4" and not aip.startswith("127."):
                    addrs.append(aip)
    return addrs


def run_module():
    result = {
        "changed": False,
        "vmid": 0,
        "addresses": [],
    }

    module = AnsibleModule(
        argument_spec={
            "api_host": {"type": "str", "required": True},
            "api_port": {"type": "int", "default": None},
            "api_user": {"type": "str", "required": True},
            "api_password": {"type": "str", "no_log": True},
            "api_token_id": {"type": "str", "no_log": True},
            "api_token_secret": {"type": "str", "no_log": True},
            "api_timeout": {"type": "int", "default": 5},
            "validate_certs": {"type": "bool", "default": False},
            "vmid": {"type": "int", "required": True},
            "timeout": {"type": "int", "default": 300},
        },
        required_together=[("api_token_id", "api_token_secret")],
        required_one_of=[("api_password", "api_token_id")],
    )

    auth_args = {"user": module.params["api_user"]}
    if not (module.params["api_token_id"] and module.params["api_token_secret"]):
        auth_args["password"] = module.params["api_password"]
    else:
        auth_args["token_name"] = module.params["api_token_id"]
        auth_args["token_value"] = module.params["api_token_secret"]

    proxmox = ProxmoxAPI(
        module.params["api_host"],
        port=module.params["api_port"],
        verify_ssl=module.params["validate_certs"],
        timeout=module.params["api_timeout"],
        **auth_args
    )

    time.sleep(1)
    vm = get_vm(module, proxmox, module.params["vmid"])
    addresses = query_vm(module, proxmox, vm)

    result["vmid"] = module.params["vmid"]
    result["addresses"] = addresses

    module.exit_json(**result)


def main():
    run_module()


if __name__ == "__main__":
    main()
