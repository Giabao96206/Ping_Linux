from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from typing import Sequence


@dataclass
class CommandResult:
    command: str
    returncode: int
    elevated: bool


class PySudoError(RuntimeError):
    """Expected application error."""


def find_sudo() -> str:
    sudo_path = shutil.which("sudo")
    if not sudo_path:
        raise PySudoError(
            "Không tìm thấy sudo trong PATH. Cài sudo trước, ví dụ: sudo apt install sudo"
        )
    return sudo_path


def current_identity() -> str:
    uid = os.geteuid()
    user = os.environ.get("USER", "unknown")
    return f"user={user}, uid={uid}" 


def is_root() -> bool:
    return os.geteuid() == 0


def build_argv(command: str, elevated: bool) -> list[str]:
    """Build argv without invoking an extra shell by default."""
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise PySudoError(f"Lỗi cú pháp command: {exc}") from exc

    if not argv:
        raise PySudoError("Command trống.")

    if elevated:
        return [find_sudo(), *argv]
    return argv


def run_command(command: str, elevated: bool = False) -> CommandResult:
    """
    Run a normal command or the same command through system sudo.

    shell=False is intentional: it avoids passing arbitrary strings to a shell.
    Use run_shell() when pipes/redirection are explicitly needed.
    """
    argv = build_argv(command, elevated)
    completed = subprocess.run(argv)
    return CommandResult(command=command, returncode=completed.returncode, elevated=elevated)


def run_shell(command: str, elevated: bool = False) -> CommandResult:
    """
    Run a shell command for pipes/redirection, e.g. 'cat file | grep hello'.

    This function executes exactly what the user types. Do not feed untrusted
    strings into it from another application.
    """
    if not command.strip():
        raise PySudoError("Command trống.")

    if elevated:
        argv = [find_sudo(), "bash", "-lc", command]
    else:
        argv = ["bash", "-lc", command]

    completed = subprocess.run(argv)
    return CommandResult(command=command, returncode=completed.returncode, elevated=elevated)


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None
