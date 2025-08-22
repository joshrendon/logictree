
.PHONY: fnmap fnmapb fnmapbat devmap

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
