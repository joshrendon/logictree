from typing import Optional
from weakref import WeakKeyDictionary

VIZ_LABEL_KEY = "viz_label"
EXPR_SOURCE_KEY = "expr_source"

_viz_labels = WeakKeyDictionary()
_expr_sources = WeakKeyDictionary()
_metric_cache = WeakKeyDictionary()

def set_viz_label(node, text: str):
    node.metadata[VIZ_LABEL_KEY] = text
    return node

def get_viz_label(node) -> Optional[str]:
    return node.metadata.get(VIZ_LABEL_KEY)

def set_expr_source(node, src: str):
    node.metadata[EXPR_SOURCE_KEY] = src
    return node

def get_expr_source(node) -> Optional[str]:
    return node.metadata.get(EXPR_SOURCE_KEY)

def cache_metrics(obj, **kvs):
    if obj not in _metric_cache:
        _metric_cache[obj] = {}
    _metric_cache[obj].update(kvs)

def get_metric(obj, key, default=None):
    return _metric_cache.get(obj, {}).get(key, default)
