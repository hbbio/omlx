"""CLI installation method and command discovery."""

import shlex
import shutil
import sys
from pathlib import Path


def is_homebrew() -> bool:
    """Return True if running inside a Homebrew-installed virtualenv."""
    return "/Cellar/" in sys.prefix or "/homebrew/" in sys.prefix


def get_install_method() -> str:
    """Return the supported installation method: homebrew or uv."""
    return "homebrew" if is_homebrew() else "uv"


def get_cli_prefix() -> str:
    """Prefer this environment's CLI when it is not already on PATH."""
    local_cli = Path(sys.executable).parent / "omlx"
    on_path = shutil.which("omlx")
    if local_cli.is_file():
        if on_path and Path(on_path).resolve() == local_cli.resolve():
            return "omlx"
        return str(local_cli)
    return "omlx"


def get_cli_command_prefix() -> str:
    """Return a shell-safe CLI command prefix for display/copy-paste."""
    return shlex.quote(get_cli_prefix())
