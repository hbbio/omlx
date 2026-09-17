<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/icon-rounded-dark.svg" width="140">
    <source media="(prefers-color-scheme: light)" srcset="docs/images/icon-rounded-light.svg" width="140">
    <img alt="oMLX" src="docs/images/icon-rounded-light.svg" width="140">
  </picture>
</p>

<h1 align="center">oMLX</h1>
<p align="center"><b>LLM inference, optimized for your Mac</b><br>Continuous batching and tiered KV caching, run from your terminal.</p>

<p align="center">
<a href="https://www.buymeacoffee.com/jundot"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="40"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License">
  <img src="https://img.shields.io/badge/python-3.11--3.13-green" alt="Python 3.11-3.13">
  <img src="https://img.shields.io/badge/platform-Apple%20Silicon-black?logo=apple" alt="Apple Silicon">
</p>

<p align="center">
  <a href="mailto:junkim.dot@gmail.com">junkim.dot@gmail.com</a> · <a href="https://omlx.ai/me">https://omlx.ai/me</a>
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#quickstart">Quickstart</a> ·
  <a href="#features">Features</a> ·
  <a href="#models">Models</a> ·
  <a href="#cli-configuration">CLI Configuration</a> ·
  <a href="https://omlx.ai/benchmarks">Benchmarks</a> ·
  <a href="https://omlx.ai">oMLX.ai</a>
</p>

<p align="center">
  <b>English</b> ·
  <a href="README.zh.md">中文</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.ja.md">日本語</a>
</p>

---

<p align="center">
  <img src="docs/images/omlx_dashboard.png" alt="oMLX Admin Dashboard" width="800">
</p>

## Install

### From Source

Requires Apple Silicon, macOS 15+, and a system installation of `uv` >= 0.12.15 (`brew install uv` if needed). This checkout uses Python 3.11 by default; 3.12 and 3.13 are also supported. `uv` downloads Python if needed, but does not install a private copy of itself.

```bash
uv sync --locked --no-dev
source .venv/bin/activate
omlx serve --model-dir ~/models
```

The default install supports text inference. Add only the features you need in the same sync command; subsequent syncs should keep the same `--extra` flags:

```bash
uv sync --locked --no-dev --extra vision --extra embeddings
```

Available extras: `vision` (also needed for TurboQuant KV cache and VLM MTP), `embeddings`, `speculative` (DFlash), `audio`, `documents`, `web-search`, `mcp`, `cluster`, `grammar`, `modelscope`, and `paroquant`. Grammar and audio add large dependency trees. The native macOS app and DMG packaging have been removed; launch the server from the CLI. The optional browser admin/chat interface remains available.

Optional native kernels for GLM-5.2, MiniMax M3, and Qwen3.5 require full Xcode with the Metal toolchain:

```bash
OMLX_WITH_CUSTOM_KERNEL=1 uv sync --locked --no-dev --reinstall-package omlx
.venv/bin/python -c "from omlx.custom_kernels import native_kernel_status; print(native_kernel_status())"
```

`uv.lock` fixes registry artifacts and Git revisions across supported Python versions. Normal installs use `--locked` and fail on stale metadata. To intentionally update dependencies, run `uv lock --upgrade`, review the lock diff, and run tests before committing it. The release-date cutoff in `pyproject.toml` must also be advanced deliberately. CI and wheel builds use the committed lock. Homebrew source archives must include it; older upstream releases do not contain this fork's changes.

Benchmark results and responses remain local. Hardware UUID collection, community uploads, automatic update checks, and the telemetry-enabling Claude cross-session option have been removed. Hugging Face and OpenTelemetry opt-outs are set before dependency imports. Model downloads, external integrations, and explicitly requested online features still use the network.

## Quickstart

### CLI

```bash
# Managed background server (Homebrew install)
omlx start
omlx stop
omlx restart

# Foreground server attached to this terminal
omlx serve --model-dir ~/models
```

The server discovers LLMs, VLMs, embedding models, and rerankers from subdirectories automatically. Any OpenAI-compatible client can connect to `http://localhost:8000/v1`. A built-in chat UI is also available at `http://localhost:8000/admin/chat`.

### Homebrew Service

If you installed via Homebrew, you can run oMLX as a managed background service:

```bash
omlx start                    # Start via brew services
omlx stop                     # Stop
omlx restart                  # Restart

brew services start omlx    # Start (auto-restarts on crash)
brew services stop omlx     # Stop
brew services restart omlx  # Restart
brew services info omlx     # Check status
```

The service runs `omlx serve` with zero-config defaults (`~/.omlx/models`, port 8000). `omlx start`, `omlx stop`, and `omlx restart` are the portable lifecycle commands; Homebrew installs delegate them to `brew services`. To customize, either set environment variables (`OMLX_MODEL_DIR`, `OMLX_PORT`, etc.) or run `omlx serve --model-dir /your/path` once to persist settings to `~/.omlx/settings.json`.

Logs are written to two locations:
- **Service log**: `$(brew --prefix)/var/log/omlx.log` (stdout/stderr)
- **Server log**: `~/.omlx/logs/server.log` (structured application log)

## Features

Supports text LLMs, vision-language models (VLM), OCR models, embeddings, and rerankers on Apple Silicon.

### Admin Dashboard

Web UI at `/admin` for real-time monitoring, model management, chat, benchmark, and per-model settings. Supports English, Korean, Japanese, Chinese, French, Russian, Spanish, and Brazilian Portuguese. All CDN dependencies are vendored for fully offline operation.

<p align="center">
  <img src="docs/images/Screenshot 2026-02-10 at 00.45.34.png" alt="oMLX Admin Dashboard" width="720">
</p>

### Experimental Multi-Mac Inference

Source builds can split one downloaded language model across unequal-memory Macs
using MLX pipeline ranks over Ring or Thunderbolt RDMA/JACCL. The Cluster
dashboard handles read-only peer discovery, strict SSH/runtime verification,
byte-aware unequal shard planning, measured compute/link rebalancing,
headroom-aware execution tuning, activation, and a live shard/performance map
on both Macs. Interactive, balanced, and throughput profiles expose coalesced
batching, prompt-cache affinity, rotating-KV limits, Ring connection tuning,
and a capability-gated experimental token-only output path. See
[Distributed inference across Macs](docs/distributed-cluster.md) for setup,
security boundaries, current limitations, and the physical-hardware validation
checklist.

### Vision-Language Models

Run VLMs with the same continuous batching and tiered KV cache stack as text LLMs. Supports multi-image chat, base64/URL/file image inputs, and tool calling with vision context. OCR models (DeepSeek-OCR, DOTS-OCR, GLM-OCR) are auto-detected with optimized prompts.

### Tiered KV Cache (Hot + Cold)

Block-based KV cache management inspired by vLLM, with prefix sharing and Copy-on-Write. The cache operates across two tiers:

- **Hot tier (RAM)**: Frequently accessed blocks stay in memory for fast access.
- **Cold tier (SSD)**: When the hot cache fills up, blocks are offloaded to SSD in safetensors format. On the next request with a matching prefix, they're restored from disk instead of recomputed from scratch - even after a server restart.

<p align="center">
  <img src="docs/images/omlx_hot_cold_cache.png" alt="oMLX Hot & Cold Cache" width="720">
</p>

### Continuous Batching

Handles concurrent requests through mlx-lm's BatchGenerator. Max concurrent requests is configurable via CLI or admin panel.

### Claude Code Optimization

Context scaling support for running smaller context models with Claude Code. Scales reported token counts so that auto-compact triggers at the right timing, and SSE keep-alive prevents read timeouts during long prefill.

### Multi-Model Serving

Load LLMs, VLMs, embedding models, and rerankers within the same server. Models are managed through a combination of automatic and manual controls:

- **LRU eviction**: Least-recently-used models are evicted automatically when memory runs low.
- **Manual load/unload**: Interactive status badges in the admin panel let you load or unload models on demand.
- **Model pinning**: Pin frequently used models to keep them always loaded.
- **Per-model TTL**: Set an idle timeout per model to auto-unload after a period of inactivity.
- **Process memory enforcement**: Total memory limit (default: system RAM - 8GB) prevents system-wide OOM.

### Per-Model Settings

Configure sampling parameters, chat template kwargs, TTL, model alias, model type override, and more per model directly from the admin panel. Changes apply immediately without server restart.

- **Model alias**: set a custom API-visible name. `/v1/models` returns the alias, and requests accept both the alias and directory name.
- **Model type override**: manually set a model as LLM or VLM regardless of auto-detection.
- **Profiles**: save named bundles of per-model settings and switch between them from the admin panel. A profile can optionally be exposed as its own model: `/v1/models` then also lists `<model>:<profile>` (e.g. `qwen3-8b:thinking`), which serves on the same engine as the base model with the profile's settings overlaid per request — no extra memory, no reload. When the base model has an alias, the exposed ID is advertised as `<alias>:<profile>`; the directory-name form keeps working, just like for the base model.

<p align="center">
  <img src="docs/images/omlx_ChatTemplateKwargs.png" alt="oMLX Chat Template Kwargs" width="480">
</p>

### Built-in Chat

Chat directly with any loaded model from the admin panel. Supports conversation history, model switching, dark mode, reasoning model output, and image upload for VLM/OCR models.

<p align="center">
  <img src="docs/images/ScreenShot_2026-03-14_104350_610.png" alt="oMLX Chat" width="720">
</p>


### Model Downloader

Search and download MLX models from HuggingFace directly in the admin dashboard. Browse model cards, check file sizes, and download with one click.

<p align="center">
  <img src="docs/images/downloader_omlx.png" alt="oMLX Model Downloader" width="720">
</p>

### Integrations

Set up OpenClaw, OpenCode, Codex, Hermes Agent, Copilot, and Pi directly from the admin dashboard with a single click. No manual config editing required.

<p align="center">
  <img src="docs/images/omlx_integrations.png" alt="oMLX Integrations" width="720">
</p>

### Performance Benchmark

One-click benchmarking from the admin panel. Measures prefill (PP) and text generation (TG) tokens per second, with partial prefix cache hit testing for realistic performance numbers.

<p align="center">
  <img src="docs/images/benchmark_omlx.png" alt="oMLX Benchmark Tool" width="720">
</p>

### API Compatibility

Drop-in replacement for OpenAI and Anthropic APIs. Supports streaming usage stats (`stream_options.include_usage`), Anthropic adaptive thinking, and vision inputs (base64, URL).

| Endpoint | Description |
|----------|-------------|
| `POST /v1/chat/completions` | Chat completions (streaming) |
| `POST /v1/completions` | Text completions (streaming) |
| `POST /v1/messages` | Anthropic Messages API |
| `POST /v1/embeddings` | Text embeddings |
| `POST /v1/rerank` | Document reranking |
| `GET /v1/models` | List available models |

### Tool Calling & Structured Output

Supports all function calling formats available in mlx-lm, JSON schema validation, and MCP tool integration. Tool calling requires the model's chat template to support the `tools` parameter. The following model families are auto-detected:

| Model Family | Format |
|---|---|
| Llama, Qwen, DeepSeek, etc. | JSON `<tool_call>` |
| Qwen3.5 Series | XML `<function=...>` |
| Gemma | `<start_function_call>` |
| GLM (4.7, 5) | `<arg_key>/<arg_value>` XML |
| MiniMax | Namespaced `<minimax:tool_call>` |
| Mistral | `[TOOL_CALLS]` |
| IFM K2 Horizon | XML or JSON inside `<ifm\|tool_calls>`. Requires `omlx[grammar]` |
| Kimi K2 | `<\|tool_calls_section_begin\|>` |
| Longcat | `<longcat_tool_call>` |

Models not listed above may still work if their chat template accepts `tools` and their output uses a recognized `<tool_call>` XML format. For tool-enabled streaming, assistant text is emitted incrementally while known tool-call control markup is suppressed from visible content; structured tool calls are emitted after parsing the completed turn.

## Models

Point `--model-dir` at a directory containing MLX-format model subdirectories. Two-level organization folders (e.g., `mlx-community/model-name/`) are also supported.

```
~/models/
├── Step-3.5-Flash-8bit/
├── Qwen3-Coder-Next-8bit/
├── gpt-oss-120b-MXFP4-Q8/
├── Qwen3.5-122B-A10B-4bit/
└── bge-m3/
```

Models are auto-detected by type. You can also download models directly from the admin dashboard.

| Type | Models |
|------|--------|
| LLM | Any model supported by [mlx-lm](https://github.com/ml-explore/mlx-lm) |
| VLM | Qwen3.5 Series, GLM-4V, Pixtral, and other [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) models |
| OCR | DeepSeek-OCR, DOTS-OCR, GLM-OCR |
| Embedding | BERT, BGE-M3, ModernBERT |
| Reranker | ModernBERT, XLM-RoBERTa |

## CLI Configuration

```bash
# Managed background server (Homebrew install)
omlx start
omlx stop
omlx restart

# Start with default settings (memory guard tier = balanced, manage via admin UI)
omlx serve --model-dir ~/models

# Choose a memory guard tier at startup
omlx serve --model-dir ~/models --memory-guard safe

# Set a custom memory guard ceiling in GB
omlx serve --model-dir ~/models --memory-guard-gb 48

# Enable SSD cache for KV blocks
omlx serve --model-dir ~/models --paged-ssd-cache-dir ~/.omlx/cache

# Set in-memory hot cache size
omlx serve --model-dir ~/models --hot-cache-max-size 20%

# Adjust max concurrent requests (default: 8)
omlx serve --model-dir ~/models --max-concurrent-requests 16

# With MCP tools
omlx serve --model-dir ~/models --mcp-config mcp.json

# HuggingFace mirror endpoint (for restricted regions)
omlx serve --model-dir ~/models --hf-endpoint https://hf-mirror.com

# API key authentication
omlx serve --model-dir ~/models --api-key your-secret-key
# Localhost-only: skip verification via admin panel global settings

# Network access requires authentication
OMLX_API_KEY=your-secret-key omlx serve --model-dir ~/models --host 0.0.0.0
```

All settings can also be configured from the web admin panel at `/admin`. Settings are persisted to `~/.omlx/settings.json`, and CLI flags take precedence.
Set the main API key before changing the server host to a LAN address or
`0.0.0.0`, or save both settings together. oMLX refuses to start on any
non-loopback address without an API key, and API key verification can only be
skipped for loopback-only binds.

<details>
<summary>Architecture</summary>

```
FastAPI Server (OpenAI / Anthropic API)
    │
    ├── EnginePool (multi-model, LRU eviction, TTL, manual load/unload)
    │   ├── BatchedEngine (LLMs, continuous batching)
    │   ├── VLMEngine (vision-language models)
    │   ├── EmbeddingEngine
    │   └── RerankerEngine
    │
    ├── ProcessMemoryEnforcer (total memory limit, TTL checks)
    │
    ├── Scheduler (FCFS, configurable concurrency)
    │   └── mlx-lm BatchGenerator
    │
    └── Cache Stack
        ├── PagedCacheManager (GPU, block-based, CoW, prefix sharing)
        ├── Hot Cache (in-memory tier, write-back)
        └── PagedSSDCacheManager (SSD cold tier, safetensors format)
```

</details>

## Development

### CLI Server

```bash
git clone https://github.com/jundot/omlx.git
cd omlx
uv sync --locked --extra vision --extra embeddings --extra speculative --extra documents --extra web-search --extra cluster
uv run --no-sync pytest -m "not slow and not integration"
```

## Contributing

Contributions are welcome! See [Contributing Guide](docs/CONTRIBUTING.md) for details.

- Bug fixes and improvements
- Performance optimizations
- Documentation improvements

## License

[Apache 2.0](LICENSE)

## Acknowledgments

- [MLX](https://github.com/ml-explore/mlx) and [mlx-lm](https://github.com/ml-explore/mlx-lm) by Apple
- [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) - Vision-language model inference on Apple Silicon
- [vllm-mlx](https://github.com/waybarrios/vllm-mlx) - oMLX started from vllm-mlx v0.1.0 and evolved significantly with multi-model serving, tiered KV caching, VLM with full paged cache support, and an admin panel
- [mlx-embeddings](https://github.com/Blaizzy/mlx-embeddings) - Embedding model support for Apple Silicon
- [dflash-mlx](https://github.com/bstnxbt/dflash-mlx) - Block diffusion speculative decoding on Apple Silicon
- [MTPLX](https://github.com/youssofal/mtplx) - Lightning MTP's verify-shape Metal kernels are powered by MTPLX by Youssof Altoukhi, which also inspired the depth-k pipeline
- [mlx-serve](https://github.com/ddalcu/mlx-serve) - The fused GDN verify prework kernel is adapted from mlx-serve's port of the mlxfast-challenge qwen35_packed_gdn_prework kernel; Qwen4 QSA's 128-bit K/V staging is adapted from mlx-serve's MIT-licensed `msv_attn_p256` kernel
