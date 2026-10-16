# Run Qwen3.8-27B-oQ4e-mtp from this checkout

The configuration and launcher are ready. The remaining steps are to build the
native kernels, start the server, and send a request. These instructions target
the local Apple M3 Max with 96 GiB RAM and the already downloaded
`scottlowry/Qwen3.8-27B-oQ4e-mtp` checkpoint.

## Files and defaults

- [Model profile](../configs/qwen38/model_settings.json): versioned starting settings.
- [Launcher](../scripts/run-qwen38.sh): checks the cached weights and native
  extension, then starts the CLI server on `127.0.0.1:8000`.
- [Example request](../configs/qwen38/chat-request.json): streaming request with
  thinking enabled and high reasoning effort.
- `.omlx-qwen38/model_settings.json`: the active configuration, already created
  in this checkout. This ignored directory also holds runtime state and caches.
  The launcher copies the starting profile only when this file is missing, so
  subsequent launches preserve your edits. Settings in `~/.omlx` are separate.

| Setting | Saved value |
| --- | --- |
| Lightning MTP | On; adaptive, up to 4 draft tokens (the current Qwen 27B minimum ceiling) |
| TurboQuant KV / SpecPrefill / DFlash | Off |
| Qwen ANE prefill | On; fixed 0.53 MLP fraction, 2048-token blocks |
| ANE topology | Single ANE for M3 Max; CPU sharing off |
| GDN prefill | Optimized GPU kernel on; ANE GDN projection on |
| ANE GDN fraction | 0.50 ceiling, capped at the model's eligible z projection |
| Context | 65536 tokens (64K) |
| Thinking / default reasoning effort | On / medium |
| Temperature / top_p / top_k | 1.0 / 0.95 / 20 |

This uses your requested fixed fraction option, rather than running an automatic
tuning pass. The separate external-drafter `vlm_mtp_enabled` option is off;
Lightning MTP uses the checkpoint's embedded MTP weights. QxA8 runtime prefill
is off for compatibility with ANE; the oQ4e checkpoint remains quantized.

## 1. Build with the system uv

Run from the checkout. Full Xcode and its Metal toolchain are required. Check
that the compiler runs: `xcrun --find metal` can find Xcode's launcher even
when the compiler component is missing. If `xcrun metal --version` reports a
missing toolchain, install it with `xcodebuild -downloadComponent MetalToolchain`.
The commands use the existing `uv` on `PATH`.

```bash
cd /Users/henri/git/omlx
command -v uv
xcrun metal --version

uv sync --locked --no-dev --extra vision --group build
OMLX_WITH_CUSTOM_KERNEL=1 uv sync --locked --no-dev --extra vision --group build \
  --no-build-isolation --reinstall-package omlx

bash scripts/run-qwen38.sh --check
```

The first sync installs the locked build tools and runtime dependencies. The
second builds oMLX's native kernels using those installed tools. Keep `--extra
vision`: this checkpoint uses the VLM engine for the requested optimized GDN
prefill path, including text-only requests. This does not install a Mac UI.
No other optional extras are needed for this profile.

The template uses `mtp_adaptive_max_depth`; upstream removed the old
`mtp_num_draft_tokens` setting. Existing runtime files still load through the
server's settings parser, which ignores retired fields and uses current defaults.

The check reads the Hugging Face cache with `local_files_only=True`, verifies
the referenced weight shards exist, and checks for the ANE native symbol. It
does not load the 27B model or prove ANE compilation will succeed. The cached
revision observed during setup was
`b8b3fa4e21f170d7296cf98401db42a4fae6bce6`; the launcher uses the locally cached
`main` revision and does not download weights. If you changed `HF_HOME` or
`HF_HUB_CACHE` since downloading, use the same cache location for the launcher.

## 2. Start the server

```bash
cd /Users/henri/git/omlx
bash scripts/run-qwen38.sh
```

Leave this terminal running; use Ctrl-C to stop. The model is pinned, so startup
loads it and eagerly compiles the ANE programs. Allow time for compilation.
The launcher enables offline Hugging Face access and disables its telemetry
and update checks. ANE prefill follows the saved model settings; supported
GDN kernels are selected by the runtime. The old GDN/ANE environment switches
were removed upstream and are no longer needed.

Check startup logs for successful MTP initialization and nonzero compiled MLP
and GDN procedure counts. Missing extensions cause the launcher to stop;
runtime ANE compilation failures can still cause fallback. ANE prefill is
experimental, uses private Apple APIs and approximate INT8 projections, and
may need a smaller fraction on this single-ANE machine. The 2048-token block
size is independent of the context limit; short tails and decoding can stay on
GPU. See the [ANE implementation notes](experimental/qwen35_ane_prefill.md)
for the runtime limits and diagnostics.

## 3. Send a request

In a second terminal:

```bash
cd /Users/henri/git/omlx
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/v1/models
curl --fail-with-body --no-buffer http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  --data-binary @configs/qwen38/chat-request.json
```

Edit the request file's `messages` for your task. Use `reasoning_effort` values
`medium`, `high`, or `xhigh`; the example uses `high`. These request fields
override the model defaults. Set `enable_thinking` to `false` for tasks that
do not need reasoning. `max_tokens: 8192` covers both reasoning and the answer;
increase it for harder tasks while leaving room for the prompt in the context.
If you enable API authentication, add `-H "Authorization: Bearer $OMLX_API_KEY"`
with your configured key to the API requests.

Clients should use base URL `http://127.0.0.1:8000/v1` and model name
`Qwen3.8-27B-oQ4e-mtp`. `top_k` and `enable_thinking` are additional request
fields; clients that support only standard OpenAI fields can rely on the
saved model defaults.

## Change context or ANE fraction

Stop the server before editing `.omlx-qwen38/model_settings.json`, then restart
with the same launcher. Edit the active file, not just the versioned starting
profile. For example, switch to 32K without changing the other settings:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path

path = Path('.omlx-qwen38/model_settings.json')
data = json.loads(path.read_text())
data['models']['scottlowry--Qwen3.8-27B-oQ4e-mtp']['max_context_window'] = 32768
path.write_text(json.dumps(data, indent=2) + '\n')
PY
bash scripts/run-qwen38.sh
```

Use `32768` or `65536` for normal use, then `131072` or up to `262144` when
needed. The [upstream model card](https://huggingface.co/Qwen/Qwen3.8-27B)
specifies 262144 as the native context window. Longer contexts increase KV
memory and prefill work; the native limit is not a memory-fit guarantee.
To adjust the ANE split, edit `qwen35_ane_prefill_fraction` in the same file.
Keep `qwen35_ane_prefill_dual_ane` false on this M3 Max.
