#
# Proxmox driver tests.
#

import contextlib
import os
import pathlib
import subprocess
import pytest
import yaml


@contextlib.contextmanager
def chdir(path):
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def molecule(command, *args):
    args = ['molecule', command] + list(args)
    proc = subprocess.Popen(args)
    rc = proc.wait()
    assert rc == 0


@pytest.mark.parametrize('scenario', [
                           'default', 'by-name', 'by-vmid', 'cloud-init',
                           'secrets-file', 'secrets-script', 'linked-clone'])
def test_molecule_test(scenario):
    print('')
    testdir = pathlib.Path(__file__).resolve().parent
    projectdir = testdir / 'proxmox_driver'
    with chdir(projectdir):
        molecule('test', '--scenario-name', scenario)
        molecule('reset')


@pytest.mark.skipif(not os.environ.get('TEST_PROXMOX_UNMANAGED_ADDRESS'),
                    reason='TEST_PROXMOX_UNMANAGED_ADDRESS is not set')
def test_unmanaged():
    print('')
    testdir = pathlib.Path(__file__).resolve().parent
    projectdir = testdir / 'proxmox_driver'
    with chdir(projectdir):
        molecule('test', '--scenario-name', 'unmanaged')
        molecule('reset')


def instance_vmids(ephemeral_directory):
    path = ephemeral_directory / 'instance_config.yml'
    with open(path) as f:
        instance_config = yaml.safe_load(f)
    return {i['instance']: int(i['vmid']) for i in instance_config}


def test_snapshot(tmp_path, monkeypatch):
    print('')
    scenario = 'snapshot'
    testdir = pathlib.Path(__file__).resolve().parent
    projectdir = testdir / 'proxmox_driver'
    # Use a known ephemeral directory to read the instance config.
    monkeypatch.setenv('MOLECULE_EPHEMERAL_DIRECTORY', str(tmp_path))
    with chdir(projectdir):
        try:
            # The first create clones and snapshots the instance.
            molecule('create', '--scenario-name', scenario)
            first = instance_vmids(tmp_path)
            # Destroy resets the instance to the snapshot, and the next
            # create uses the same instance.
            molecule('destroy', '--scenario-name', scenario)
            molecule('create', '--scenario-name', scenario)
            second = instance_vmids(tmp_path)
            assert second == first
            molecule('converge', '--scenario-name', scenario)
        finally:
            # Remove the instance.
            monkeypatch.setenv('MOLECULE_PROXMOX_SNAPSHOT', 'false')
            molecule('destroy', '--scenario-name', scenario)
            molecule('reset', '--scenario-name', scenario)


def test_template_not_found():
    print('')
    scenario = 'template-not-found'
    testdir = pathlib.Path(__file__).resolve().parent
    projectdir = testdir / 'proxmox_driver'
    with chdir(projectdir):
        try:
            args = ['molecule', 'create', '--scenario-name', scenario]
            proc = subprocess.run(args, capture_output=True, text=True)
            print(proc.stdout)
            print(proc.stderr)
            assert proc.returncode != 0
            expected = ("Template 'molecule-test-no-such-template' "
                        "not found on node")
            assert expected in proc.stdout + proc.stderr
        finally:
            molecule('destroy', '--scenario-name', scenario)
            molecule('reset')
