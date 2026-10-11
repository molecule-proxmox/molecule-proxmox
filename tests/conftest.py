#
# Run the tests with a fake Proxmox server, instead of a real Proxmox
# cluster, with the --fake option:
#
#    tox -e latest -- --fake
#
# The fake Proxmox API server runs in the pytest process, and the fake
# virtual machines are podman containers. The fake vms are given addresses
# in the 192.0.2.0/24 documentation range, and the ssh connections to them
# are made with 'podman exec', with a ProxyCommand in an ssh config file
# given to ansible with ANSIBLE_SSH_ARGS. The TEST_PROXMOX_* environment
# variables are set to use the fake Proxmox server.
#

import os
import pathlib
import shutil
import subprocess
import sys
import logging
import tempfile

import pytest

TESTS_DIR = pathlib.Path(__file__).resolve().parent
FAKE_DIR = TESTS_DIR / 'fake'
SCENARIOS_DIR = TESTS_DIR / 'proxmox_driver' / 'molecule'
UNMANAGED_ADDRESS = '192.0.2.250'

_fake = None
_workdir = None


def pytest_addoption(parser):
    parser.addoption(
        '--fake', action='store_true',
        help='Use a fake Proxmox server and podman containers for the '
             'virtual machines, instead of a real Proxmox cluster.')


def pytest_configure(config):
    # Set up the fake environment before the test modules are imported, so
    # the skipif conditions see the fake environment variables.
    global _fake, _workdir
    if not config.getoption('--fake'):
        return
    if not shutil.which('podman'):
        pytest.exit('The --fake option requires podman.', returncode=1)

    sys.path.insert(0, str(FAKE_DIR))
    import fake_proxmox

    _workdir = tempfile.mkdtemp(prefix='molecule-proxmox-fake-')
    workdir = pathlib.Path(_workdir)
    handler = logging.FileHandler(workdir / 'fake_proxmox.log')
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    fake_proxmox.log.addHandler(handler)
    fake_proxmox.log.setLevel(logging.DEBUG)
    subprocess.run(['podman', 'build', '--quiet', '--tag', fake_proxmox.IMAGE,
                    str(FAKE_DIR)], check=True, stdout=subprocess.DEVNULL)

    key = workdir / 'id_ed25519'
    subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f',
                    str(key)], check=True)
    pubkey = key.with_suffix('.pub')
    pubkey.chmod(0o644)

    ssh_config = workdir / 'ssh_config'
    ssh_config.write_text(
        'Host 192.0.2.*\n'
        '    ProxyCommand podman exec -i fakevm-%h /usr/sbin/sshd -i\n')

    _fake = fake_proxmox.FakeProxmox(str(pubkey), workdir=str(workdir))
    _fake.start()

    # An existing machine for the unmanaged instance test.
    _fake.cluster.cleanup()
    subprocess.run(
        ['podman', 'run', '--detach', '--name', f'fakevm-{UNMANAGED_ADDRESS}',
         '--hostname', 'unmanaged', '--label', fake_proxmox.LABEL,
         '--init', '--no-hosts', '--cap-add', 'SYS_ADMIN',
         '--volume', f'{pubkey}:/home/molecule/.ssh/authorized_keys:ro,Z',
         fake_proxmox.IMAGE],
        check=True, stdout=subprocess.DEVNULL)

    env = {
        'TEST_PROXMOX_HOST': f'{_fake.host}:{_fake.port}',
        'TEST_PROXMOX_PORT': str(_fake.port),
        'TEST_PROXMOX_USER': 'root@pam',
        'TEST_PROXMOX_PASSWORD': 'fake',
        'TEST_PROXMOX_VALIDATE_CERTS': 'false',
        'TEST_PROXMOX_NODE': fake_proxmox.NODES[0],
        'TEST_PROXMOX_TEMPLATE_NAME': fake_proxmox.TEMPLATE_NAME,
        'TEST_PROXMOX_TEMPLATE_VMID':
            str(fake_proxmox.TEMPLATE_VMIDS[fake_proxmox.NODES[0]]),
        'TEST_PROXMOX_SSH_USER': 'molecule',
        'TEST_PROXMOX_SSH_IDENTITY_FILE': str(key),
        'TEST_PROXMOX_SECRETS_FILE':
            str(SCENARIOS_DIR / 'secrets-file' / 'secrets-file.yml'),
        'TEST_PROXMOX_SECRETS_SCRIPT':
            str(SCENARIOS_DIR / 'secrets-script' / 'secrets.sh'),
        'TEST_PROXMOX_DEBUG': 'false',
        'TEST_PROXMOX_UNMANAGED_ADDRESS': UNMANAGED_ADDRESS,
        'TEST_PROXMOX_UNMANAGED_SSH_USER': '',
        'TEST_PROXMOX_UNMANAGED_SSH_PORT': '',
        'TEST_PROXMOX_UNMANAGED_SSH_IDENTITY_FILE': '',
        'ANSIBLE_SSH_ARGS': f'-F {ssh_config} -o ControlMaster=auto '
                            '-o ControlPersist=60s',
    }
    os.environ.update(env)


@pytest.fixture(autouse=True)
def fake_ephemeral_directory(request, tmp_path, monkeypatch):
    """Use a separate molecule ephemeral directory for each test.

    The molecule ephemeral directory of a scenario is shared by all of
    the molecule runs of the project, so use a separate one with the fake
    Proxmox server, to not interfere with a test run with a real Proxmox
    cluster.
    """
    if _fake:
        monkeypatch.setenv('MOLECULE_EPHEMERAL_DIRECTORY', str(tmp_path))


def pytest_unconfigure(config):
    global _fake, _workdir
    if _fake:
        _fake.stop()
        _fake = None
    if _workdir:
        if getattr(config, '_fake_failed', False):
            print(f'\nFake Proxmox files kept in {_workdir}')
        else:
            shutil.rmtree(_workdir, ignore_errors=True)
        _workdir = None


def pytest_sessionfinish(session, exitstatus):
    session.config._fake_failed = exitstatus != 0
