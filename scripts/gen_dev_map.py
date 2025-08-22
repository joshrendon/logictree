#!/usr/bin/env python3
"""
Generate docs/dev_map.md — a Markdown TOC of classes/functions with docstring snippets.
Optional env:
  GITHUB_URL_BASE="https://github.com/joshua/logictree/blob/main"
"""

from __future__ import annotations
import ast, os, textwrap
from pathlib import Path
from typing import Iterable

SRC = Path("src/logictree")
OUT = Path("docs/dev_map.md")
GITHUB = os.environ.get("GITHUB_URL_BASE")  # e.g., https://github.com/<USER>/logictree/blob/main

def iter_py_files(root: Path) -> Iterable[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())

def anchor_for(path: Path, line: int) -> str:
    rel = path.as_posix()
    return f"{GITHUB}/{rel}#L{line}" if GITHUB else f"{rel}#L{line}"

def firstline(ds: str | None) -> str:
    if not ds:
        return ""
    s = textwrap.dedent(ds).strip().splitlines()
    return s[0] if s else ""

def fmt_sig(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args = []
    for a in fn.args.args:
        args.append(a.arg)
    if fn.args.vararg:
        args.append("*" + fn.args.vararg.arg)
    for a in fn.args.kwonlyargs:
        # show kw-only presence; values omitted to keep this compact
        args.append(a.arg + "=")
    if fn.args.kwarg:
        args.append("**" + fn.args.kwarg.arg)
    return f"{fn.name}({', '.join(args)})"

def collect(path: Path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))
    items = {"module": firstline(ast.get_docstring(tree)), "classes": [], "funcs": []}

    # top-level functions: col_offset == 0 (heuristic)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            items["funcs"].append((node.lineno, fmt_sig(node), firstline(ast.get_docstring(node))))
        elif isinstance(node, ast.ClassDef):
            methods = []
            for b in node.body:
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append((b.lineno, fmt_sig(b), firstline(ast.get_docstring(b))))
            items["classes"].append((node.lineno, node.name, firstline(ast.get_docstring(node)), sorted(methods)))
    items["classes"].sort(key=lambda t: t[0])
    items["funcs"].sort(key=lambda t: t[0])
    return items

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Logictree Developer Map",
        "",
        "_Auto-generated overview of modules, classes, and functions under `src/logictree/`._",
        "",
        f"Source root: `{SRC}`",
        "",
        "---",
        ""
    ]
    for f in iter_py_files(SRC):
        items = collect(f)
        if not items["classes"] and not items["funcs"] and not items["module"]:
            continue
        rel = f.relative_to(Path("."))
        lines.append(f"## `{rel}`")
        if items["module"]:
            lines.append(f"> {items['module']}")
            lines.append("")
        # Top-level functions
        if items["funcs"]:
            lines.append("### Functions")
            for ln, sig, doc in items["funcs"]:
                link = anchor_for(f, ln)
                tail = f" — _{doc}_" if doc else ""
                lines.append(f"- [{sig}]({link})  _(L{ln})_{tail}")
            lines.append("")
        # Classes + methods
        if items["classes"]:
            lines.append("### Classes")
            for ln, cname, cdoc, methods in items["classes"]:
                clink = anchor_for(f, ln)
                ctail = f" — _{cdoc}_" if cdoc else ""
                lines.append(f"- [{cname}]({clink})  _(L{ln})_{ctail}")
                for mln, msig, mdoc in methods:
                    mlink = anchor_for(f, mln)
                    mtail = f" — _{mdoc}_" if mdoc else ""
                    lines.append(f"  - [{msig}]({mlink})  _(L{mln})_{mtail}")
            lines.append("")
        lines.append("---\n")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
