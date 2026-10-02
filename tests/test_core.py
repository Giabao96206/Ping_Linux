import os

from pysudo.core import build_argv, current_identity, is_root


def test_build_argv_normal():
    assert build_argv("ls -la /tmp", elevated=False) == ["ls", "-la", "/tmp"]


def test_build_argv_sudo():
    argv = build_argv("id", elevated=True)
    assert argv[-1] == "id"
    assert os.path.basename(argv[0]) == "sudo"


def test_identity_helpers():
    assert isinstance(current_identity(), str)
    assert is_root() in {True, False}
