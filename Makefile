PY ?= python
SCRIPTS_DIR := $(abspath ..)

.PHONY: help build-all build-practico build-taller clean

help:
	@echo "Uso (desde la carpeta padre /Scripts):"
	@echo "  make -C _pdf build-all"
	@echo "  make -C _pdf build-practico"
	@echo "  make -C _pdf build-taller"
	@echo "  make -C _pdf clean"

build-all:
	cd "$(SCRIPTS_DIR)" && $(PY) -m _pdf.build_all

build-practico:
	cd "$(SCRIPTS_DIR)" && $(PY) -m _pdf.build_all --area practico

build-taller:
	cd "$(SCRIPTS_DIR)" && $(PY) -m _pdf.build_all --area taller

clean:
	$(PY) -c "import shutil; from pathlib import Path; p=Path(__file__).resolve().parent; \
		shutil.rmtree(p/'output'/'_cache', ignore_errors=True)"
