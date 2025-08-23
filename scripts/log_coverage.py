#!/usr/bin/env python3
"""
Coverage logger that DOES NOT require XML.

It will try in order:
  1) coverage JSON (data/coverage.json or --cov-json path)
  2) .coverage data file(s) via coverage.py API (combines shards if found)

It can also read pytest's JSON report for pass/fail counts.

Examples:
  # with pytest-cov
  pytest --cov=sv_ast --cov-branch --cov-report=term-missing:skip-covered \
         --json-report --json-report-file data/pytest_report.json || true
  python log_coverage.py --out data/coverage_log.csv

  # if you have coverage JSON already:
  coverage json -o data/coverage.json
  python log_coverage.py --cov-json data/coverage.json --out data/coverage_log.csv

Optional args:
  --cov-json PATH          path to a coverage.json (from `coverage json`)
  --pytest-json PATH       path to pytest JSON report (defaults to data/pytest_report.json if exists)
  --out PATH               output CSV path (required)
  --timestamp ISO8601      override timestamp
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(description="Append coverage/test metrics to a CSV without needing XML.")
    p.add_argument("--out", required=True, help="Output CSV path (e.g., data/coverage_log.csv)")
    p.add_argument("--cov-json", help="Optional coverage.json (from `coverage json`)")
    p.add_argument("--pytest-json", help="Optional pytest JSON report; defaults to data/pytest_report.json if present")
    p.add_argument("--timestamp", help="Override timestamp (ISO-8601). Defaults to now()")
    return p.parse_args()

def read_coverage_json(path: Path):
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        print(f"[warn] Could not read coverage JSON at {path}: {e}", file=sys.stderr)
        return None
    # coverage.py >= 6: top-level 'totals'
    totals = data.get("totals") or {}
    covered = totals.get("covered_lines")
    num_stmts = totals.get("num_statements")
    pct = totals.get("percent_covered")
    if covered is not None and num_stmts is not None:
        if pct is None:
            pct = 0.0 if not num_stmts else 100.0 * (covered / num_stmts)
        return int(num_stmts), int(covered), float(pct)
    # fallback schema: try nested totals under "files" aggregation
    try:
        covered = sum(f["summary"]["covered_lines"] for f in data.get("files", {}).values())
        num_stmts = sum(f["summary"]["num_statements"] for f in data.get("files", {}).values())
        pct = 0.0 if not num_stmts else 100.0 * covered / num_stmts
        return int(num_stmts), int(covered), float(pct)
    except Exception:
        return None

def read_coverage_datafile():
    """Use coverage.py API to analyze .coverage data file(s)."""
    try:
        import coverage
    except Exception:
        print("[warn] coverage module not available; cannot read .coverage data", file=sys.stderr)
        return None

    cov = coverage.Coverage()
    # If parallel shards exist, combine them first
    try:
        cov.combine()   # searches for .coverage.* by default
        cov.save()
    except Exception:
        pass

    try:
        cov.load()
    except Exception as e:
        print(f"[warn] Could not load .coverage data: {e}", file=sys.stderr)
        return None

    data = cov.get_data()
    files = list(data.measured_files())
    if not files:
        return (0, 0, 0.0)

    total_stmts = 0
    covered_stmts = 0
    for fn in files:
        try:
            # analysis2 returns: (filename, statements, excluded, missing, branches)
            _, statements, _excluded, missing, _branches = cov.analysis2(fn)
            total_stmts += len(statements)
            covered_stmts += len(statements) - len(missing)
        except Exception:
            # Some files may be missing sources, ignore them
            continue

    pct = 0.0 if total_stmts == 0 else 100.0 * covered_stmts / total_stmts
    return int(total_stmts), int(covered_stmts), float(pct)

def read_pytest_json(py_path: Path | None):
    if py_path is None:
        # auto-discover default
        default = Path("data/pytest_report.json")
        if default.exists():
            py_path = default
        else:
            return 0, 0, ""  # no counts
    try:
        data = json.loads(py_path.read_text())
    except Exception as e:
        print(f"[warn] Could not read pytest JSON at {py_path}: {e}", file=sys.stderr)
        return 0, 0, ""
    summary = (data or {}).get("summary", {})
    passed = int(summary.get("passed", 0) or 0)
    failed = int(summary.get("failed", 0) or 0)
    errors = int(summary.get("error", 0) or summary.get("errors", 0) or 0)
    total = int(summary.get("total", 0) or summary.get("collected", 0) or 0)
    return passed, failed + errors, total or (passed + failed + errors)

def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def safe_append_row(out_csv: Path, header: list[str], row_map: dict):
    ensure_parent(out_csv)
    if not out_csv.exists():
        with out_csv.open("w", newline="") as f:
            import csv
            w = csv.writer(f)
            w.writerow(header)
            w.writerow([row_map.get(h, "") for h in header])
        return
    with out_csv.open("r", newline="") as f:
        import csv
        r = csv.reader(f)
        try:
            existing = next(r)
        except StopIteration:
            existing = header
    if existing != header:
        print(f"[warn] Header mismatch in {out_csv}. Aligning to existing columns: {existing}", file=sys.stderr)
        ordered = [row_map.get(h, "") for h in existing]
        with out_csv.open("a", newline="") as f:
            csv.writer(f).writerow(ordered)
        return
    with out_csv.open("a", newline="") as f:
        import csv
        csv.writer(f).writerow([row_map.get(h, "") for h in header])

def main():
    args = parse_args()
    out_csv = Path(args.out)
    cov_json_path = Path(args.cov_json) if args.cov_json else None
    pytest_json_path = Path(args.pytest_json) if args.pytest_json else None

    # 1) Try coverage JSON if provided or common default
    totals = None
    tried_sources = []
    if cov_json_path and cov_json_path.exists():
        totals = read_coverage_json(cov_json_path); tried_sources.append(str(cov_json_path))
    elif Path("data/coverage.json").exists():
        totals = read_coverage_json(Path("data/coverage.json")); tried_sources.append("data/coverage.json")

    # 2) Fallback to .coverage data via coverage API
    if totals is None:
        tried_sources.append(".coverage (API)")
        totals = read_coverage_datafile()

    if totals is None:
        print("[error] No coverage totals available. Tried: " + ", ".join(tried_sources), file=sys.stderr)
        sys.exit(2)

    total_stmts, covered_stmts, percent = totals
    passed, failed, total_tests = read_pytest_json(pytest_json_path)

    timestamp = args.timestamp or dt.datetime.now().isoformat(timespec="seconds")
    row = {
        "timestamp": timestamp,
        "coverage": round(percent, 2),
        "tests_passed": passed,
        "tests_failed": failed,
        "total": total_tests,
        "total_statements": total_stmts,
        "covered_statements": covered_stmts,
    }
    header = ["timestamp","coverage","tests_passed","tests_failed","total","total_statements","covered_statements"]
    safe_append_row(out_csv, header, row)

    print(f"[+] Logged: {out_csv}")
    print(f"    time={timestamp} coverage={percent:.2f}%  tests: passed={passed} failed={failed}")

if __name__ == "__main__":
    main()
