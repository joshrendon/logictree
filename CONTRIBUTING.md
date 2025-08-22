## Developer quick start

```bash
# One-time
pip install -e '.[dev]'

# tight loop
make test            # fast markers (unit/props/diff)
make lint            # ruff
make typecheck       # mypy
make coverage        # coverage + htmlcov/

# handy maps
make fnmap           # class/def atlas (ripgrep + less)
make fnmapbat        # atlas with highlighted source lines
make devmap          # generate docs/dev_map.md (AST-based)
```

Optional: If you use `direnv`, `fnmap`, `fnmapbat`, and `devmap` become commands when you `cd` into repo.
Otherwise use `make` or call scripts directly.
