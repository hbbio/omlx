#!/bin/bash
# Launch the cached Qwen model using this checkout's private runtime settings.
set -euo pipefail
umask 077

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ $# -gt 1 || ( $# -eq 1 && "$1" != "--check" ) ]]; then
    echo "Usage: bash scripts/run-qwen38.sh [--check]" >&2
    exit 2
fi

if [[ ! -x .venv/bin/python || ! -x .venv/bin/omlx ]]; then
    echo "Build the environment first; see docs/run-qwen38.md." >&2
    exit 1
fi

mkdir -p .omlx-qwen38
if [[ ! -f .omlx-qwen38/model_settings.json ]]; then
    cp configs/qwen38/model_settings.json .omlx-qwen38/model_settings.json
fi

export HF_HUB_OFFLINE=1
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_UPDATE_CHECK=1
export DO_NOT_TRACK=1
export OTEL_SDK_DISABLED=true
export OMLX_QWEN35_ANE_PREFILL=1
export OMLX_GDN_KERNEL=1
export OMLX_GDN_IMPL=blocked_seq

.venv/bin/python - <<'PY'
import importlib.util
import json
from pathlib import Path

from huggingface_hub import snapshot_download
from omlx.model_settings import ModelSettings, SETTINGS_VERSION, validate_ane_prefill

model_id = "scottlowry--Qwen3.8-27B-oQ4e-mtp"
config = json.loads(Path(".omlx-qwen38/model_settings.json").read_text())
if config["version"] != SETTINGS_VERSION:
    raise SystemExit("Unsupported model settings version; see docs/run-qwen38.md.")
settings = ModelSettings(**config["models"][model_id])
validate_ane_prefill(settings.to_dict(), "qwen3_5")
if not 1 <= settings.max_context_window <= 262144:
    raise SystemExit("Context must be between 1 and 262144 tokens.")

snapshot = Path(snapshot_download(
    "scottlowry/Qwen3.8-27B-oQ4e-mtp", local_files_only=True,
))
index = json.loads((snapshot / "model.safetensors.index.json").read_text())
missing = sorted({name for name in index["weight_map"].values()
                  if not (snapshot / name).is_file()})
if missing:
    raise SystemExit(f"Incomplete cached model; missing shards: {missing}")
print(f"Cached model: {snapshot}")
print(f"Context limit: {settings.max_context_window} tokens")

if importlib.util.find_spec("mlx_vlm") is None:
    raise SystemExit("The vision extra is required; see docs/run-qwen38.md.")
try:
    from omlx.custom_kernels.qwen35_prefill import fast
except ImportError as exc:
    raise SystemExit(f"Cannot load the Qwen kernels (Metal access is required): {exc}")

if not fast.is_native_available() or not fast.has_symbol("qwen35_ane_compile_linear"):
    raise SystemExit(
        "Qwen ANE native kernels are unavailable. Follow the build steps in "
        f"docs/run-qwen38.md. Import detail: {fast.import_error()}"
    )
print("Qwen ANE native extension is available; runtime compilation is checked on load.")
PY

if [[ "${1:-}" == "--check" ]]; then
    exit 0
fi

exec .venv/bin/omlx serve \
    --base-path "$repo_root/.omlx-qwen38" \
    --hf-cache \
    --host 127.0.0.1 \
    --port 8000
