# SPDX-License-Identifier: Apache-2.0
"""Regression tests for the Homebrew formula and its release automation.

The release workflow must update only the formula's top-level source URL and
checksum. Resource blocks have independent checksums that must survive version
bumps (issues #2151 and #2173).

macOS 27 betas broke `brew install omlx` in several ways (issue #2110):

- dyld now requires the LC_SYMTAB string pool in Mach-O libraries to be
  8-byte aligned, so prebuilt Rust wheels (e.g. tokenizers) fail dlopen.
- The beta `strip` binary corrupts dynamic offsets in Mach-O libraries
  (llvm/llvm-project#203678), so Cargo/maturin release stripping and
  Homebrew's post-install clean pass must be kept away from the dylibs.
- CMake's default Python discovery can pick a newer unlinked system
  Python instead of the formula's venv when building custom kernels.
- The custom-kernel verification ran from the build directory, where the
  raw omlx/ source tree shadows the installed package.
- Later pip steps (mlx-audio, python-multipart) ran without --no-binary,
  so a prebuilt wheel could clobber a source-built package, and pip's
  wheel cache could resurrect a dylib built before the strip guards.

The formula and workflow use Ruby and shell syntax, so these are text-level
assertions that the guards stay present.
"""

import re
from pathlib import Path

import pytest

from omlx.custom_kernels import NATIVE_KERNEL_PACKAGES

FORMULA_PATH = Path(__file__).resolve().parents[1] / "Formula" / "omlx.rb"
WORKFLOW_PATH = (
    Path(__file__).resolve().parents[1] / ".github" / "workflows" / "update-formula.yml"
)

MACOS_27_GUARD = 'MacOS.version >= "27"'


@pytest.fixture(scope="module")
def formula() -> str:
    return FORMULA_PATH.read_text()


@pytest.fixture(scope="module")
def formula_update_workflow() -> str:
    return WORKFLOW_PATH.read_text()


class TestFormulaReleaseUpdate:
    def test_source_sha_update_is_scoped_to_top_level(self, formula_update_workflow):
        """Release bumps must not replace checksums inside resource blocks."""
        sha_update = next(
            line.strip()
            for line in formula_update_workflow.splitlines()
            if line.lstrip().startswith("sed -i") and "steps.sha.outputs.sha256" in line
        )

        assert "s|^  sha256" in sha_update
        assert '"$|  sha256' in sha_update


class TestMacOS27Workarounds:
    def test_tokenizers_built_from_source_on_macos_27(self, formula):
        """Rust wheels with 4-byte-aligned LINKEDIT must be rebuilt natively."""
        assert MACOS_27_GUARD in formula
        assert 'no_binary += ",tokenizers"' in formula

    def test_base_no_binary_list_unconditional(self, formula):
        """Older macOS keeps the existing source-build list unchanged."""
        assert 'no_binary = "cohere_melody,pydantic-core,rpds-py,tiktoken"' in formula
        assert '["--no-binary-package", name]' in formula

    def test_release_stripping_disabled_on_macos_27(self, formula):
        """The beta strip binary corrupts dylibs; Cargo/maturin must not strip."""
        assert 'ENV["CARGO_PROFILE_RELEASE_STRIP"] = "false"' in formula
        assert 'ENV["MATURIN_STRIP"] = "false"' in formula

    def test_homebrew_clean_pass_skipped_on_macos_27(self, formula):
        """Homebrew's clean pass also runs strip over the venv's dylibs."""
        assert "on_macos do" in formula
        assert f'skip_clean "libexec" if {MACOS_27_GUARD}' in formula

    def test_uv_cache_bypassed_on_macos_27(self, formula):
        """Pip reuses locally built wheels even under --no-binary, so a
        wheel cached before the strip guards existed stays corrupted."""
        assert 'uv_flags << "--no-cache"' in formula


class TestCustomKernelBuild:
    def test_formula_covers_every_native_kernel_package(self, formula):
        """Source checks and import verification must cover every extension."""
        match = re.search(
            r"^\s*CUSTOM_KERNELS = %w\[([^]]+)\]\.freeze$", formula, re.MULTILINE
        )

        assert match is not None
        assert tuple(match.group(1).split()) == NATIVE_KERNEL_PACKAGES
        assert "kernel_sources = CUSTOM_KERNELS.map" in formula
        assert "for package in #{CUSTOM_KERNELS.inspect}:" in formula

    def test_cmake_pinned_to_venv_python(self, formula):
        """CMake must not discover a stray system Python for kernel builds."""
        assert "-DPython_EXECUTABLE=#{libexec}/bin/python" in formula

    def test_kernel_verification_not_shadowed_by_buildpath(self, formula):
        """Import check must run outside buildpath's raw omlx/ source tree."""
        assert "Dir.chdir(libexec)" in formula

    def test_metal_toolchain_checked_before_kernel_build(self, formula):
        block = formula.index('if build.with?("custom-kernel")')
        guard = formula.index('quiet_system("/usr/bin/xcrun", "-f", "metal")', block)
        assert guard < formula.index('ENV["OMLX_WITH_CUSTOM_KERNEL"]', block)


class TestLockedUvInstall:
    def test_single_locked_runtime_install(self, formula):
        assert 'depends_on "uv" => :build' in formula
        assert 'Formula["uv"].opt_bin/"uv"' in formula
        assert '"sync", "--locked", "--no-dev", "--no-editable"' in formula
        assert 'ENV["UV_PROJECT_ENVIRONMENT"] = libexec' in formula
        assert 'ENV["UV_PYTHON_DOWNLOADS"] = "never"' in formula
        assert "bin/pip" not in formula
        assert 'resource "mlx-audio"' not in formula
