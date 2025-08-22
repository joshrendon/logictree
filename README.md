## Logictree: SystemVerilog Static Logic Analyzer — Project Status Summary
[![Tests](https://github.com/<USER>/logictree/actions/workflows/ci.yml/badge.svg)](https://github.com/<USER>/logictree/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Logictree is a Python toolkit and IR for parsing, lowering, and analyzing SystemVerilog logic:
- Lower `case → if → mux` with equivalence checks
- Canonicalize to primitive gates; depth & gate-count analysis
- Graphviz rendering, JSON export, and CLI

## Install (dev)
```bash
pip install -e .
```

## CLI
`logictree --help`

## Run Tests (fast set)
`pytest -q -m "unit or props or diff"`

## Project layout
```
src/logictree/        # core library
src/sv_parser/        # parser front-end
src/cli/              # CLI entrypoint
src/gui/              # explorer (optional)
tests/{unit,props,diff,integ}/
```
## Docs & dashboards
* Coverage dashboard (static): `coverage_dashboard/`
* Golden circuits: `golden_circuits/`

---
Philosophy and Use Case

This tool is designed for symbolic logic analysis, enabling:
* Pre-synthesis decoder optimization
* RTL logic depth estimation
* Visualization of complex Boolean expressions
* Research and educational insight into logic structure

It’s especially suited to analyzing RISC-V instruction decoders, and will serve as the foundation 
for future articles, tutorials, and FPGA validation studies.

Generating new visitor modules from grammar:
cd grammar/
antlr -Dlanguage=Python3 <grammar.g4>
antlr -Dlanguage=Python3 -visitor <grammar.g4>  # To generate a visitor file

# 2) Badges & likely needed links
- **CI Badge** `.github/workflows/ci.yml`: https://github.com/joshrendon/logictree/actions/workflows/ci.yml/badge.svg
- **GH Pages:** https://joshrendon.github.io/logictree/
- **PyPi: ** https://img.shields.io/pypi/v/logictree.svg

