# Makefile for logictree (src/ layout, pytest markers)

# --- Config -------------------------------------------------------------------
PYTHON ?= python
PIP    ?= $(PYTHON) -m pip

PKG        := logictree
SRC_DIR    := src/$(PKG)
TEST_DIR   := tests
COV_HTML   := coverage/html
COV_TERM   := term-missing

# Default marker sets
FAST_MARK  := "unit or props or diff"
FULL_MARK  := "unit or props or diff or slow or mutation"

ANTLR_JAR := antlr-4.13.1-complete.jar
GRAMMAR_DIR := grammar
PARSER_OUT := src/sv_parser
GRAMMAR := $(GRAMMAR_DIR)/SystemVerilogSubset.g4

# --- Phony targets ------------------------------------------------------------
.PHONY: help install dev clean lint format typecheck test test-fast test-full \
        coverage coverage-ok cov cov-html fnmap fnmapb fnmapbat devmap build dist \
		gen-parser clean-parser

# --- Help ---------------------------------------------------------------------
help:
	@echo "Common targets:"
	@echo "  make install      - editable install (no dev extras)"
	@echo "  make dev          - editable install with [dev] extras"
	@echo "  make test-fast    - pytest with FAST markers ($(FAST_MARK))"
	@echo "  make test         - alias for test-fast"
	@echo "  make test-full    - pytest with FULL markers ($(FULL_MARK))"
	@echo "  make coverage     - run tests (FAST) with coverage"
	@echo "  make coverage-ok  - run tests (FAST) with coverage-ok (always succeed)"
	@echo "  make cov-html     - open htmlcov/ (if generated)"
	@echo "  make gen-parser   - generate parser scripts from antlr4 grammar"
	@echo "  make clean-parser - clean parser scripts"
	@echo "  make lint         - ruff check"
	@echo "  make format       - ruff format"
	@echo "  make typecheck    - mypy on src/"
	@echo "  make fnmap        - quick map of classes/defs (rg + less)"
	@echo "  make fnmapb       - quick map of classes/defs (rg + bat --language=python)"
	@echo "  make fnmapbat     - map with highlighted lines (rg + bat)"
	@echo "  make devmap       - generate docs/dev_map.md (AST-based)"
	@echo "  make clean        - remove caches, build artifacts"
	@echo "  make build        - build wheel/sdist (requires 'build')"
	@echo "  make dist         - alias for build"

# --- Env setup ----------------------------------------------------------------
install:
	$(PIP) install -e .

dev:
	$(PIP) install -e '.[dev]'

# --- Quality gates ------------------------------------------------------------
lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy $(SRC_DIR)

# --- Tests --------------------------------------------------------------------
test-fast:  ## fast dev loop
	pytest -q -m $(FAST_MARK) --maxfail=1 --durations=15

test: test-fast

test-full:  ## full suite (nightly / local deep run)
	pytest -q -m $(FULL_MARK) --durations=25

# --- Coverage -----------------------------------------------------------------
# Strict: fails if tests fail, but still writes htmlcov/
#
FFAST_MARK = unit or props or diff
coverage:
	pytest -q -m '$(FFAST_MARK)' \
	  --cov --cov-report=term-missing --cov-report=html; \
	rc=$$?; \
	echo "HTML coverage report at htmlcov/index.html"; \
	exit $$rc

# Non-strict local helper: always succeeds (good during refactors)
coverage-ok:
	pytest -q -m $(FAST_MARK) --cov --cov-report=term-missing --cov-report=html || true
	@echo "HTML coverage report at htmlcov/index.html"

cov: coverage
	@echo "HTML coverage report at htmlcov/index.html"

cov-html:
	@xdg-open htmlcov/index.html 2>/dev/null || open htmlcov/index.html || true

cov-clean:
	@rm -rf .coverage* htmlcov .pytest_cache

# --- Gen parser
gen-parser:
	@echo "Generating Python parser from $(GRAMMAR)..."
	@if [ ! -f $(ANTLR_JAR) ]; then \
	  echo "Downloading ANTLR jar..."; \
	  curl -L -o $(ANTLR_JAR) https://www.antlr.org/download/$(ANTLR_JAR); \
	fi
	# Run ANTLR inside grammar/, output to grammar/
	cd $(GRAMMAR_DIR) && java -jar ../$(ANTLR_JAR) -Dlanguage=Python3 -visitor $(notdir $(GRAMMAR))
	# Move Python outputs into src/sv_parser/
	@mv $(GRAMMAR_DIR)/*.py $(PARSER_OUT)/
	# Clean up leftover .tokens and .interp
	@rm -f $(GRAMMAR_DIR)/*.tokens $(GRAMMAR_DIR)/*.interp

clean-parser:
	@echo "Cleaning generated ANTLR files from $(PARSER_OUT)..."
	rm -f $(PARSER_OUT)/*Lexer.py \
	      $(PARSER_OUT)/*Parser.py \
	      $(PARSER_OUT)/*Listener.py \
	      $(PARSER_OUT)/*Visitor.py

# --- Dev helpers (your scripts) -----------------------------------------------
fnmap:
	scripts/bin/fnmap

fnmapb:
	scripts/bin/fnmapb

fnmapbat:
	scripts/bin/fnmapbat

devmap:
	python scripts/gen_dev_map.py
	@echo "Wrote docs/dev_map.md"
	@command -v bat >/dev/null 2>&1 && bat docs/dev_map.md || cat docs/dev_map.md

# --- Build/publish (optional) -------------------------------------------------
build dist:
	$(PYTHON) -m build

# --- Clean --------------------------------------------------------------------
clean:
	@find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.pyc' -delete
	@rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov build dist *.egg-info coverage *.log
