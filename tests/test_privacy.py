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
from omlx.patches.qwen35_yarn import apply_qwen35_yarn_patch
apply_qwen35_yarn_patch()

# Exercise text prefill, batching, and decode without any optional packages.
from mlx_lm.generate import BatchGenerator
from mlx_lm.models.llama import Model, ModelArgs
model = Model(ModelArgs(
    model_type='llama', hidden_size=32, num_hidden_layers=1,
    intermediate_size=64, num_attention_heads=4,
    rms_norm_eps=1e-5, vocab_size=64,
))
generator = BatchGenerator(model, max_tokens=2)
try:
    uids = generator.insert([[1, 2, 3], [4, 5]])
    responses = []
    for _ in range(5):
        batch = generator.next_generated()
        if not batch:
            break
        responses.extend(batch)
    assert len(responses) == 4, responses
    assert {response.uid for response in responses} == set(uids)
finally:
    generator.close()

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
