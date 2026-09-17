# SPDX-License-Identifier: Apache-2.0
"""Privacy defaults must take effect before third-party packages initialize."""

import os
import subprocess
import sys


def test_privacy_defaults_and_minimal_server_import():
    # A fresh interpreter avoids hiding import-order bugs behind pytest's imports.
    script = """
import importlib.abc
import os
import sys

class NoOptionalPackages(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, *args):
        if fullname.split('.')[0] in {
            'mlx_vlm', 'mlx_audio', 'mlx_embeddings', 'dflash_mlx',
            'markitdown', 'ddgs', 'uv', 'venvstacks',
        }:
            raise ModuleNotFoundError(fullname, name=fullname)

sys.meta_path.insert(0, NoOptionalPackages())
import omlx
for key in ('HF_HUB_DISABLE_TELEMETRY', 'DO_NOT_TRACK', 'HF_HUB_DISABLE_UPDATE_CHECK'):
    assert os.environ[key] == '1', key
assert os.environ['OTEL_SDK_DISABLED'] == 'true'
from huggingface_hub import constants
assert constants.HF_HUB_DISABLE_TELEMETRY
import omlx.server
import asyncio
from omlx.engine.vlm import VLMBatchedEngine
engine = object.__new__(VLMBatchedEngine)
engine._loaded = False
try:
    asyncio.run(engine.start())
except ImportError as exc:
    assert 'uv sync --locked --no-dev --extra vision' in str(exc)
else:
    raise AssertionError('Vision start unexpectedly succeeded without its extra')
"""
    env = dict(
        os.environ,
        HF_HUB_DISABLE_TELEMETRY="0",
        DO_NOT_TRACK="0",
        HF_HUB_DISABLE_UPDATE_CHECK="0",
        OTEL_SDK_DISABLED="false",
    )
    subprocess.run([sys.executable, "-c", script], env=env, check=True, timeout=60)
