# SPDX-License-Identifier: Apache-2.0
"""Verify offline assets and fail closed when downloads do not match the lock."""

import hashlib
import importlib.util
import io
import re
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "omlx_web_vendor_deps", Path(__file__).resolve().parents[1] / "vendor_deps.py"
)
vendor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vendor)


def test_all_locked_assets_and_katex_font_references():
    for relative, locked in vendor.VENDOR_LOCK.items():
        data = (vendor.STATIC / relative).read_bytes()
        assert hashlib.sha256(data).hexdigest() == locked["sha256"], relative
    css = (vendor.STATIC / "css/katex.min.css").read_text()
    for relative in re.findall(r"url\((fonts/[^)]+)\)", css):
        assert (vendor.STATIC / "css" / relative).is_file(), relative
        assert "css/" + relative in vendor.VENDOR_LOCK


@pytest.mark.parametrize("existing", [False, True])
def test_tampered_assets_are_rejected(tmp_path, monkeypatch, existing):
    monkeypatch.setattr(vendor, "STATIC", tmp_path)
    monkeypatch.setattr(
        vendor,
        "VENDOR_LOCK",
        {
            "test.js": {
                "url": "https://example.invalid/test.js",
                "sha256": hashlib.sha256(b"reviewed").hexdigest(),
            }
        },
    )
    dest = tmp_path / "test.js"
    if existing:
        dest.write_bytes(b"tampered")
    monkeypatch.setattr(
        vendor.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"tampered")
    )
    with pytest.raises(RuntimeError, match="Integrity check failed"):
        vendor._download("https://example.invalid/test.js", dest)
    if not existing:
        assert not dest.exists()


def test_unreviewed_download_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(vendor, "STATIC", tmp_path)
    with pytest.raises(RuntimeError, match="No reviewed download hash"):
        vendor._download("https://example.invalid/new.js", tmp_path / "new.js")
