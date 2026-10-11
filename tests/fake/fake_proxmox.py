#
# Fake Proxmox VE API server for the molecule-proxmox tests.
#
# Implements the subset of the Proxmox VE API used by the driver
# playbooks and modules, with an in-memory cluster. The fake virtual
# machines are podman containers, created from the fake-vm image, so
# molecule can connect to them with ssh. See conftest.py for how the
# ssh connections are made.
#
# The fake cluster has two nodes, each with a local copy of a template
# with the same name, like a real cluster with several nodes.
#
# Usage (for manual testing):
#
#    python3 fake_proxmox.py --port 8006 --pubkey ~/.ssh/id_ed25519.pub
#

import argparse
import http.server
import itertools
import json
import logging
import os
import re
import ssl
import subprocess
import tempfile
import threading
import time
import urllib.parse

log = logging.getLogger("fake_proxmox")

IMAGE = "localhost/molecule-proxmox-fake-vm:latest"
LABEL = "molecule-proxmox-fake"
VERSION = {"version": "8.2.4", "release": "8.2", "repoid": "faketest"}
NODES = ["pve1", "pve2"]
TEMPLATE_NAME = "debian"
TEMPLATE_VMIDS = {"pve1": 9000, "pve2": 9001}
ADDRESS_PREFIX = "192.0.2."  # TEST-NET-1, never routed.


class ApiError(Exception):
    """An API error, returned with the message as the HTTP reason phrase."""

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def podman(*args, check=True):
    log.debug("podman %s", " ".join(args))
    return subprocess.run(
        ["podman", *args], check=check, capture_output=True, text=True
    )


def container_name(address):
    """The ssh ProxyCommand finds the container by the vm address."""
    return f"fakevm-{address}"


class FakeCluster:
    """In-memory Proxmox cluster with podman containers for running vms."""

    def __init__(self, pubkey, label=LABEL, image=IMAGE):
        self.pubkey = pubkey
        self.label = label
        self.image = image
        self.lock = threading.RLock()
        self.vms = {}
        self.tasks = {}
        self.task_counter = itertools.count(1)
        self.address_counter = itertools.count(10)
        for node, vmid in TEMPLATE_VMIDS.items():
            self.vms[vmid] = {
                "vmid": vmid,
                "name": TEMPLATE_NAME,
                "node": node,
                "template": 1,
                "status": "stopped",
                "config": {"name": TEMPLATE_NAME, "template": 1},
                "snapshots": {},
                "hostname": TEMPLATE_NAME,
                "address": None,
            }

    # --- Helpers

    def vm(self, node, vmid):
        vmid = int(vmid)
        vm = self.vms.get(vmid)
        if not vm or vm["node"] != node:
            raise ApiError(
                500,
                f"Configuration file 'nodes/{node}/qemu-server/{vmid}.conf'"
                " does not exist",
            )
        return vm

    def task(self, node, kind, vmid, exitstatus="OK"):
        """Tasks complete immediately."""
        number = next(self.task_counter)
        start = int(time.time())
        upid = (
            f"UPID:{node}:{number:08X}:00000000:{start:08X}"
            f":{kind}:{vmid}:root@pam:"
        )
        self.tasks[upid] = {"node": node, "exitstatus": exitstatus}
        return upid

    def start_container(self, vm):
        if vm["address"] is None:
            vm["address"] = ADDRESS_PREFIX + str(next(self.address_counter))
        name = container_name(vm["address"])
        if vm.get("container"):
            # Restart the container of a stopped vm.
            podman("start", name)
        else:
            # Remove any stale container left from a previous test run.
            podman("rm", "--force", name, check=False)
            vm["container"] = True
            podman(
                "run",
                "--detach",
                "--name",
                name,
                "--hostname",
                vm["hostname"],
                "--label",
                self.label,
                "--init",
                "--no-hosts",
                "--cap-add",
                "SYS_ADMIN",
                "--volume",
                f"{self.pubkey}:/home/molecule/.ssh/authorized_keys:ro,Z",
                self.image,
            )

    def stop_container(self, vm):
        if vm["address"]:
            podman(
                "stop",
                "--time",
                "1",
                container_name(vm["address"]),
                check=False,
            )

    def remove_container(self, vm):
        if vm["address"]:
            podman("rm", "--force", container_name(vm["address"]), check=False)
        vm["container"] = False

    def resource(self, vm):
        r = {
            "id": f"qemu/{vm['vmid']}",
            "type": "qemu",
            "vmid": vm["vmid"],
            "name": vm["name"],
            "node": vm["node"],
            "status": vm["status"],
            "template": vm["template"],
        }
        if vm["config"].get("tags"):
            r["tags"] = vm["config"]["tags"]
        return r

    def cleanup(self):
        """Remove all of the fake vm containers."""
        out = podman(
            "ps",
            "--all",
            "--quiet",
            "--filter",
            f"label={self.label}",
            check=False,
        ).stdout.split()
        if out:
            podman("rm", "--force", *out, check=False)

    # --- API

    def handle(self, method, path, args):
        with self.lock:
            return self._handle(method, path, args)

    def _handle(self, method, path, args):  # noqa: C901
        p = [urllib.parse.unquote(x) for x in path.strip("/").split("/")]
        route = (method, *p)

        if route == ("POST", "access", "ticket"):
            return {
                "ticket": "PVE:fake",
                "CSRFPreventionToken": "fake",
                "username": args.get("username", ""),
            }
        if route == ("GET", "version"):
            return VERSION
        if route == ("GET", "nodes"):
            return [
                {"node": n, "status": "online", "type": "node"} for n in NODES
            ]
        if route == ("GET", "cluster", "resources"):
            return [self.resource(vm) for vm in self.vms.values()]
        if route == ("GET", "cluster", "nextid"):
            return str(
                max([100, *[vmid + 1 for vmid in self.vms if vmid < 9000]])
            )
        if route in (("GET", "pools"), ("GET", "storage")):
            return []

        if len(p) >= 2 and p[0] == "nodes":
            node = p[1]
            if node not in NODES:
                raise ApiError(500, f"hostname lookup '{node}' failed")
            rest = p[2:]
            if method == "GET" and rest == ["qemu"]:
                return [
                    {
                        "vmid": vm["vmid"],
                        "name": vm["name"],
                        "status": vm["status"],
                        "template": vm["template"],
                    }
                    for vm in self.vms.values()
                    if vm["node"] == node
                ]
            if len(rest) >= 2 and rest[0] == "tasks":
                task = self.tasks.get(rest[1])
                if not task:
                    raise ApiError(500, f"no such task '{rest[1]}'")
                if rest[2:] == ["status"]:
                    return {
                        "upid": rest[1],
                        "node": node,
                        "status": "stopped",
                        "exitstatus": task["exitstatus"],
                    }
                if rest[2:] == ["log"]:
                    return [{"n": 1, "t": f"TASK {task['exitstatus']}"}]
            if len(rest) >= 2 and rest[0] == "qemu":
                return self.handle_vm(method, node, rest[1], rest[2:], args)

        raise ApiError(
            501,
            f"Method '{method} /{path.strip('/')}' not implemented"
            " by the fake Proxmox API",
        )

    def handle_vm(self, method, node, vmid, rest, args):  # noqa: C901
        vm = self.vm(node, vmid)
        vmid = vm["vmid"]
        route = (method, *rest)

        if route == ("POST", "clone"):
            newid = int(args.get("newid") or 0)
            if newid in self.vms:
                raise ApiError(
                    500,
                    f"unable to create VM {newid}: config file already exists",
                )
            target = args.get("target") or node
            config = dict(
                vm["config"], name=args.get("name", f"Copy-of-VM-{vm['name']}")
            )
            config.pop("template", None)
            for key in ("pool", "full"):
                if key in args:
                    config[key] = args[key]
            self.vms[newid] = {
                "vmid": newid,
                "name": config["name"],
                "node": target,
                "template": 0,
                "status": "stopped",
                "config": config,
                "snapshots": {},
                "hostname": vm["hostname"],
                "address": None,
            }
            return self.task(node, "qmclone", vmid)
        if route == ("GET", "config"):
            return dict(vm["config"])
        if route in (("PUT", "config"), ("POST", "config")):
            vm["config"].update(args)
            if "name" in args:
                vm["name"] = args["name"]
            for key in [
                k.strip()
                for k in args.get("delete", "").split(",")
                if k.strip()
            ]:
                vm["config"].pop(key, None)
            vm["config"].pop("delete", None)
            return (
                None if method == "PUT" else self.task(node, "qmconfig", vmid)
            )
        if route == ("DELETE",):
            if vm["status"] == "running":
                raise ApiError(500, f"VM {vmid} is running - destroy failed")
            self.remove_container(vm)
            del self.vms[vmid]
            return self.task(node, "qmdestroy", vmid)
        if route == ("GET", "status", "current"):
            return {
                "vmid": vmid,
                "name": vm["name"],
                "status": vm["status"],
                "qmpstatus": vm["status"],
            }
        if route == ("POST", "status", "start"):
            if vm["template"]:
                raise ApiError(500, f"VM {vmid} is a template")
            if vm["status"] == "running":
                return self.task(
                    node,
                    "qmstart",
                    vmid,
                    exitstatus=f"VM {vmid} already running",
                )
            self.start_container(vm)
            vm["status"] = "running"
            return self.task(node, "qmstart", vmid)
        if route in (
            ("POST", "status", "stop"),
            ("POST", "status", "shutdown"),
        ):
            self.stop_container(vm)
            vm["status"] = "stopped"
            return self.task(node, "qmstop", vmid)
        if route == ("GET", "snapshot"):
            snaps = [
                {
                    "name": s["name"],
                    "description": s["description"],
                    "snaptime": s["snaptime"],
                }
                for s in vm["snapshots"].values()
            ]
            return snaps + [
                {
                    "name": "current",
                    "description": "You are here!",
                    "running": int(vm["status"] == "running"),
                }
            ]
        if route == ("POST", "snapshot"):
            name = args["snapname"]
            if name in vm["snapshots"]:
                raise ApiError(500, f"snapshot name '{name}' already used")
            vm["snapshots"][name] = {
                "name": name,
                "description": args.get("description", ""),
                "snaptime": int(time.time()),
                "config": dict(vm["config"]),
            }
            return self.task(node, "qmsnapshot", vmid)
        if (
            len(rest) == 3
            and rest[0] == "snapshot"
            and rest[2] == "rollback"
            and method == "POST"
        ):
            snap = vm["snapshots"].get(rest[1])
            if not snap:
                raise ApiError(500, f"snapshot '{rest[1]}' does not exist")
            # The fake snapshots capture the state before the first boot,
            # so a rollback discards the container.
            self.remove_container(vm)
            vm["status"] = "stopped"
            vm["config"] = dict(snap["config"])
            vm["name"] = vm["config"].get("name", vm["name"])
            return self.task(node, "qmrollback", vmid)
        if route == ("GET", "agent", "network-get-interfaces"):
            if vm["status"] != "running":
                raise ApiError(500, f"VM {vmid} is not running")
            return {
                "result": [
                    {
                        "name": "lo",
                        "ip-addresses": [
                            {
                                "ip-address-type": "ipv4",
                                "ip-address": "127.0.0.1",
                                "prefix": 8,
                            }
                        ],
                    },
                    {
                        "name": "eth0",
                        "ip-addresses": [
                            {
                                "ip-address-type": "ipv4",
                                "ip-address": vm["address"],
                                "prefix": 24,
                            }
                        ],
                    },
                ]
            }

        raise ApiError(
            501,
            f"Method '{method} /nodes/{node}/qemu/{vmid}/{'/'.join(rest)}'"
            " not implemented by the fake Proxmox API",
        )


class Handler(http.server.BaseHTTPRequestHandler):
    cluster = None  # Set by FakeProxmox.

    def log_message(self, fmt, *args):
        log.debug("%s - %s", self.address_string(), fmt % args)

    def _respond(self, method):
        url = urllib.parse.urlsplit(self.path)
        args = dict(urllib.parse.parse_qsl(url.query))
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            body = self.rfile.read(length).decode()
            args.update(urllib.parse.parse_qsl(body, keep_blank_values=True))
        path = re.sub(r"^/api2/json", "", url.path)
        log.info("%s %s %s", method, path, args)
        try:
            data = self.cluster.handle(method, path, args)
            status, reason, payload = 200, "OK", {"data": data}
        except ApiError as e:
            log.info("error %s %s", e.status, e.message)
            # Proxmox returns the error message as the HTTP reason phrase.
            status, reason, payload = e.status, e.message, {"data": None}
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.exception("internal error")
            status, reason, payload = (
                500,
                f"fake proxmox internal error: {e}",
                {"data": None},
            )
        body = json.dumps(payload).encode()
        self.send_response(status, reason)
        self.send_header("Content-Type", "application/json;charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._respond("GET")

    def do_POST(self):
        self._respond("POST")

    def do_PUT(self):
        self._respond("PUT")

    def do_DELETE(self):
        self._respond("DELETE")


class FakeProxmox:
    """Run the fake Proxmox API with https in a background thread."""

    def __init__(self, pubkey, host="127.0.0.1", port=0, workdir=None):
        self.cluster = FakeCluster(pubkey)
        self.workdir = workdir or tempfile.mkdtemp(prefix="fake-proxmox-")
        handler = type(
            "FakeProxmoxHandler", (Handler,), {"cluster": self.cluster}
        )
        self.server = http.server.ThreadingHTTPServer((host, port), handler)
        self.server.daemon_threads = True
        self.server.socket = self._ssl_context().wrap_socket(
            self.server.socket, server_side=True
        )
        self.host, self.port = self.server.server_address[:2]
        self.thread = None

    def _ssl_context(self):
        cert = os.path.join(self.workdir, "cert.pem")
        key = os.path.join(self.workdir, "key.pem")
        subprocess.run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-subj",
                "/CN=localhost",
                "-days",
                "2",
                "-keyout",
                key,
                "-out",
                cert,
            ],
            check=True,
            capture_output=True,
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        return context

    def start(self):
        self.thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.thread.start()
        return self

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.cluster.cleanup()


def main():
    parser = argparse.ArgumentParser(description="Fake Proxmox VE API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8006)
    parser.add_argument(
        "--pubkey", required=True, help="ssh public key for the fake vms"
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    fake = FakeProxmox(
        os.path.abspath(args.pubkey), args.host, args.port
    ).start()
    print(f"fake proxmox listening on https://{fake.host}:{fake.port}")
    try:
        fake.thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        fake.stop()


if __name__ == "__main__":
    main()
