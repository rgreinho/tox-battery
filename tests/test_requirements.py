# std
import os
import subprocess
import textwrap

# local
from toxbat import requirements

# 3rd-party
import pytest


def test_is_changed_fails_on_missing_req_file():
    with pytest.raises(ValueError):
        requirements.is_changed('nonexisting/requirements.txt',
                                'nonexisting/requirements.txt')


def test_venv_recreated_on_requirements_file_update(tmpdir):
    """Ensure environment recreated on requirements file changed."""
    # given
    tmpdir = tmpdir.strpath
    path = lambda *args: os.path.join(tmpdir, *args)
    update_file(path('tox.ini'), textwrap.dedent('''
        [tox]
        skipsdist=True

        [testenv]
        deps = -rreq1/requirements.txt
        commands = {posargs}
    '''))
    update_file(path('req1/requirements.txt'), 'pytest-xdist==1.13.0\n')

    # excercise
    run('tox -- python -V'.split(), tmpdir)
    assert_package_intalled(tmpdir, package='pytest-xdist', version='1.13')
    update_file(path('req1/requirements.txt'), 'pytest-xdist==1.13.1\n')
    run('tox -- python -V'.split(), tmpdir)

    # verify
    assert_package_intalled(tmpdir, package='pytest-xdist', version='1.13.1')


def assert_package_intalled(toxini_dir, package, version):
    _, output, _ = run('tox -- pip freeze'.split(), toxini_dir,
                       capture_output=True)
    expected_line = "{0}=={1}".format(package, version)
    assert expected_line in output


def run(cmd, working_dir, ok_return_codes=(0,), capture_output=False):
    p = subprocess.Popen(cmd,
                         cwd=working_dir,
                         stdout=capture_output and subprocess.PIPE or None,
                         stderr=capture_output and subprocess.PIPE or None)
    (stdout, stderr) = p.communicate()
    if not capture_output:
        stdout, stderr = '', ''

    if p.returncode not in ok_return_codes:
        raise Exception("Failed to execute 'tox' with return code {0}: {0}"
                        .format(p.returncode, stdout + stderr))
    return p.returncode, str(stdout), str(stderr)


def update_file(fpath, content):
    fdir = os.path.dirname(fpath)
    if fdir and not os.path.isdir(fdir):
        os.makedirs(fdir)
    with open(fpath, 'w') as fd:
        fd.write(content)
