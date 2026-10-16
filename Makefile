# Developer shortcuts use the same locked environment as CLI installs and CI.
UV ?= uv
PYTHON ?= .venv/bin/python
# Pass optional capabilities as EXTRAS="--extra vision --extra audio", etc.
EXTRAS ?=

.PHONY: install install-no-kernels mcp dev dev-no-kernels kernels clean-kernels web

# Editable CLI install with the browser UI and native custom kernels.
install: install-no-kernels
	$(MAKE) kernels

# Install without kernels for machines without full Xcode.
install-no-kernels:
	$(UV) sync --locked --no-dev $(EXTRAS)

mcp:
	$(UV) sync --locked --no-dev --extra mcp $(EXTRAS)

dev: dev-no-kernels
	$(MAKE) kernels

dev-no-kernels:
	$(UV) sync --locked --extra vision --extra embeddings --extra documents --extra web-search --extra cluster $(EXTRAS)

# Keep installed extras while adding the locked native build tools.
kernels: clean-kernels
	$(UV) sync --locked --no-dev --group build --inexact $(EXTRAS)
	OMLX_WITH_CUSTOM_KERNEL=1 $(PYTHON) setup.py build_ext --inplace --force
	$(PYTHON) -c "from omlx.custom_kernels import native_kernel_status; \
	failed = {k: v['import_error'] for k, v in native_kernel_status().items() if not v['available']}; \
	print(failed or 'All native custom kernels are available.'); raise SystemExit(1 if failed else 0)"

clean-kernels:
	rm -f omlx/custom_kernels/*/*.so omlx/custom_kernels/*/*.dylib omlx/custom_kernels/*/*.metallib
	rm -rf build/temp.*/omlx.custom_kernels.* build/lib*/omlx/custom_kernels

web:
	$(PYTHON) apps/omlx-web/build_css.py
	$(PYTHON) apps/omlx-web/normalize_i18n.py
