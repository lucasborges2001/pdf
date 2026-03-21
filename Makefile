PY ?= python
SCRIPTS_DIR := $(abspath ..)

.PHONY: help build check scan clean

help:
	@echo "Uso (desde la carpeta padre /Scripts):"
	@echo "  make -C _pdf build"
	@echo "  make -C _pdf check"
	@echo "  make -C _pdf scan"
	@echo "  make -C _pdf clean"

build:
	cd "$(SCRIPTS_DIR)" && $(PY) -m _pdf.build

check:
	cd "$(SCRIPTS_DIR)" && $(PY) -m _pdf.build --check

scan:
	cd "$(SCRIPTS_DIR)" && $(PY) -m _pdf.scan --input

clean:
	$(PY) -c "import shutil; from pathlib import Path; p=Path(__file__).resolve().parent; \
		shutil.rmtree(p/'output'/'_cache', ignore_errors=True)"
