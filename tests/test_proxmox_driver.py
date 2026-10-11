#
# Proxmox driver tests.
#

import contextlib
import os
import pathlib
import subprocess
import pytest


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
