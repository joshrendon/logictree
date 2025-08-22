# LogicTree Phase 1 Checklist

This checklist tracks the remaining work and priorities for completing Phase 1 of the LogicTree project.

---

## ✅ Completed

- [x] Implement core IR (`LogicOp`, `LogicVar`, `LogicConst`, etc.)
- [x] Implement `.depth()` and `.delay()` with caching
- [x] Lower `CaseStatement → IfStatement` with semantic preservation
- [x] CLI for graphviz, DOT, JSON output
- [x] Plot coverage data with `matplotlib` (PNG/HTML)
- [x] `log_coverage.py` supports timestamped CSV and plots
- [x] Graph output validated for original and lowered forms

---

## 🔄 In Progress

- [ ] `free_vars()` support across all node types
- [ ] `.writes()` and `.writes_must()` for RW tracking
- [ ] `if → mux` lowering implementation
- [ ] `simplify()` logic expansion
- [ ] Refactor CLI into `cli/commands.py`

---

## ⏭️ Next Up

- [ ] Add `.to_sympy()` backend
- [ ] Expand tests for all RW edge cases
- [ ] Canonical simplification of logic expressions
- [ ] CLI flags for lowering passes (`--lower-if`, `--lower-mux`, etc.)
- [ ] CLI tests: full parse → lower → output flow

---

## 🧪 Optional (Phase 2)

- [ ] `to_verilog()` RTL round-trip support
- [ ] `to_bdd()` backend
- [ ] GUI / Jupyter / web explorer mode
- [ ] Rewriting DSL for transformation scripting
- [ ] Quantitative subexpression reuse metrics

---

## 🧹 Housekeeping

- [ ] Write README.md
- [ ] Document IR node structure
- [ ] Move test utils into `tests/utils/`
- [ ] Organize sample Verilog files into `testdata/`
