# logictree/utils/overlay.py


class OverlayRegistry:
    def __init__(self):
        self._label_registry = {}
        self._expr_source_registry = {}
        self._metric_cache = {}

    def set_label(self, node, label: str):
        self._label_registry[id(node)] = label

    def get_label(self, node) -> str:
        if id(node) in self._label_registry:
            return self._label_registry[id(node)]

        # fallback: try introspection
        if hasattr(node, "name"):
            return str(getattr(node, "name"))
        if hasattr(node, "value"):
            return str(getattr(node, "value"))
        return type(node).__name__

    def has_label(self, node) -> bool:
        return id(node) in self._label_registry

    def set_expr_source(self, node, text: str):
        self._expr_source_registry[id(node)] = text

    def get_expr_source(self, node) -> str | None:
        return self._expr_source_registry.get(id(node), None)

    def cache_metrics(self, node, **metrics):
        self._metric_cache.setdefault(id(node), {}).update(metrics)

    def get_metric(self, node, key, default=None):
        return self._metric_cache.get(id(node), {}).get(key, default)

    def clear_all(self):
        self._label_registry.clear()
        self._expr_source_registry.clear()
        self._metric_cache.clear()


# Export a singleton instance
overlay = OverlayRegistry()

# Expose methods from the singleton overlay registry
get_label = overlay.get_label
set_label = overlay.set_label
has_label = overlay.has_label
clear_all = overlay.clear_all
