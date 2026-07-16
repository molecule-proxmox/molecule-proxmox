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
    with subprocess.Popen(args) as proc:
        rc = proc.wait()

    assert rc == 0


def test_molecule_init_scenario(tmpdir):
    print('')
    with chdir(tmpdir):
        molecule('init', 'scenario', '--driver-name', 'molecule-proxmox')
        assert pathlib.Path('molecule/default/converge.yml').exists()
        assert pathlib.Path('molecule/default/create.yml').exists()
        assert pathlib.Path('molecule/default/destroy.yml').exists()
        assert pathlib.Path('molecule/default/molecule.yml').exists()


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
