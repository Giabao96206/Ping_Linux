from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path

from .core import PySudoError, current_identity, is_root, run_command, run_shell

BANNER = r"""
=========================================
        PySudo Terminal 0.1.0
=========================================
Educational sudo-like terminal frontend
Type 'help' for commands.
""".strip("\n")

HELP = """
Các lệnh:
  run <command>         Chạy command với user hiện tại
  sudo <command>        Chạy command qua sudo hệ thống
  shell <command>       Chạy command bằng bash với user hiện tại
  root-shell            Mở bash thông qua sudo
  id                    Xem UID/EUID hiện tại
  pwd                   Xem thư mục hiện tại
  cd <path>             Đổi thư mục
  history               Xem lịch sử trong phiên
  clear                 Xóa màn hình
  help                  Hiện trợ giúp
  exit / quit           Thoát

Ví dụ:
  sudo apt update
  sudo ls -la /root
  shell "ls -la | grep py"
  root-shell
""".strip()


class TerminalApp:
    def __init__(self) -> None:
        self.history: list[str] = []

    def prompt(self) -> str:
        marker = "#" if is_root() else "$"
        cwd = Path.cwd().name or "/"
        return f"pysudo:{cwd}{marker} "

    def dispatch(self, line: str) -> bool:
        line = line.strip()
        if not line:
            return True

        self.history.append(line)

        try:
            parts = shlex.split(line)
        except ValueError as exc:
            print(f"Lỗi cú pháp: {exc}", file=sys.stderr)
            return True

        command = parts[0]
        rest = line[len(command):].strip()

        if command in {"exit", "quit"}:
            return False

        if command == "help":
            print(HELP)
            return True

        if command == "id":
            print(current_identity())
            return True

        if command == "pwd":
            print(Path.cwd())
            return True

        if command == "cd":
            if not rest:
                target = os.path.expanduser("~")
            else:
                target = os.path.expanduser(rest)
            try:
                os.chdir(target)
            except OSError as exc:
                print(f"cd: {exc}", file=sys.stderr)
            return True

        if command == "history":
            for i, item in enumerate(self.history, 1):
                print(f"{i:>3}  {item}")
            return True

        if command == "clear":
            print("\033[2J\033[H", end="")
            return True

        if command == "run":
            if not rest:
                print("Cú pháp: run <command>")
                return True
            self._execute(rest, elevated=False, shell=False)
            return True

        if command == "sudo":
            if not rest:
                print("Cú pháp: sudo <command>")
                return True
            self._execute(rest, elevated=True, shell=False)
            return True

        if command == "shell":
            if not rest:
                print("Cú pháp: shell <command>")
                return True
            self._execute(rest, elevated=False, shell=True)
            return True

        if command == "root-shell":
            self._root_shell()
            return True

        # Convenience: behave like a normal terminal for ordinary commands.
        self._execute(line, elevated=False, shell=False)
        return True

    def _execute(self, command: str, elevated: bool, shell: bool) -> None:
        try:
            result = run_shell(command, elevated=elevated) if shell else run_command(command, elevated=elevated)
        except FileNotFoundError:
            print(f"Không tìm thấy command: {command.split()[0]}", file=sys.stderr)
            return
        except PySudoError as exc:
            print(f"Lỗi: {exc}", file=sys.stderr)
            return

        if result.returncode != 0:
            print(f"[PySudo] command kết thúc với exit code {result.returncode}", file=sys.stderr)

    def _root_shell(self) -> None:
        try:
            run_command("bash", elevated=True)
        except (FileNotFoundError, PySudoError) as exc:
            print(f"Không thể mở root shell: {exc}", file=sys.stderr)

    def repl(self) -> int:
        print(BANNER)
        while True:
            try:
                line = input(self.prompt())
            except EOFError:
                print()
                return 0
            except KeyboardInterrupt:
                print("^C")
                continue

            if not self.dispatch(line):
                return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pysudo",
        description="Educational sudo-like terminal frontend in Python.",
    )
    parser.add_argument(
        "--once",
        metavar="COMMAND",
        help="Chạy một command rồi thoát.",
    )
    parser.add_argument(
        "--sudo",
        action="store_true",
        help="Kết hợp với --once để chạy command qua sudo.",
    )
    parser.add_argument(
        "--shell",
        action="store_true",
        help="Kết hợp với --once để chạy command qua bash.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    app = TerminalApp()

    if args.once is None:
        return app.repl()

    try:
        if args.sudo:
            result = run_shell(args.once, elevated=True) if args.shell else run_command(args.once, elevated=True)
        else:
            result = run_shell(args.once, elevated=False) if args.shell else run_command(args.once, elevated=False)
    except (PySudoError, FileNotFoundError) as exc:
        print(f"pysudo: {exc}", file=sys.stderr)
        return 1

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
