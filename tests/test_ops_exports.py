def test_ops_exports_are_aggregated():
    # Import the package itself
    import logictree.nodes.ops as ops_pkg

    # These should be re-exported from submodules via __init__.py
    from logictree.nodes.ops import LogicOp, LogicConst, LogicVar, AndOp, OrOp, NotOp

    # Basic presence checks
    for name in ["LogicOp", "LogicConst", "LogicVar", "AndOp", "OrOp", "NotOp"]:
        assert name in ops_pkg.__all__, f"{name} missing from ops package __all__"
        assert getattr(ops_pkg, name), f"{name} not found as attribute on ops package"
