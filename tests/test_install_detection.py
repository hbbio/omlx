"""Tests for CLI command resolution and Homebrew service detection."""

from unittest.mock import patch

from omlx.utils.install import (
    get_cli_command_prefix,
    get_cli_prefix,
    get_install_method,
    is_homebrew,
)


def test_homebrew_service_detection():
    with patch(
        "omlx.utils.install.sys.prefix", "/opt/homebrew/Cellar/omlx/1.0/libexec"
    ):
        assert is_homebrew()
        assert get_install_method() == "homebrew"
    with patch("omlx.utils.install.sys.prefix", "/tmp/project/.venv"):
        assert not is_homebrew()
        assert get_install_method() == "uv"


def test_command_uses_current_environment_and_quotes_spaces(tmp_path):
    bin_dir = tmp_path / "my project" / ".venv" / "bin"
    bin_dir.mkdir(parents=True)
    cli = bin_dir / "omlx"
    cli.touch()
    with (
        patch("omlx.utils.install.sys.executable", str(bin_dir / "python")),
        patch("omlx.utils.install.shutil.which", return_value=None),
    ):
        assert get_cli_prefix() == str(cli)
        assert get_cli_command_prefix() == "'" + str(cli) + "'"


def test_public_symlink_to_environment_uses_short_command(tmp_path):
    cli = tmp_path / "omlx"
    cli.touch()
    public = tmp_path / "public"
    public.symlink_to(cli)
    with (
        patch("omlx.utils.install.sys.executable", str(tmp_path / "python")),
        patch("omlx.utils.install.shutil.which", return_value=str(public)),
    ):
        assert get_cli_command_prefix() == "omlx"
