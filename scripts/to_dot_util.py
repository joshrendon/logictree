import graphviz
from sv_parser.ast_nodes import BinaryOp, UnaryOp, IdNode, Number, Assign, Module, CaseStatement, CaseItem

def to_dot(ast):
    dot = graphviz.Digraph(comment="SystemVerilog AST")
    node_count = [0]  # use list to make it mutable in nested scope

    def next_id():
        node_count[0] += 1
        return f"n{node_count[0]}"

    def visit(node):
        if isinstance(node, BinaryOp):
            my_id = next_id()
            dot.node(my_id, node.op)
            left_id = visit(node.left)
            right_id = visit(node.right)
            dot.edge(my_id, left_id)
            dot.edge(my_id, right_id)
            return my_id

        elif isinstance(node, UnaryOp):
            my_id = next_id()
            dot.node(my_id, node.op)
            child_id = visit(node.operand)
            dot.edge(my_id, child_id)
            return my_id

        elif isinstance(node, IdNode):
            my_id = next_id()
            dot.node(my_id, node.name)
            return my_id

        elif isinstance(node, Number):
            my_id = next_id()
            dot.node(my_id, str(node.value))
            return my_id

        elif isinstance(node, Assign):
            my_id = next_id()
            dot.node(my_id, f"assign\n{node.target}")
            expr_id = visit(node.source)
            dot.edge(my_id, expr_id)
            return my_id

        elif isinstance(node, CaseStatement):
            my_id = next_id()
            dot.node(my_id, "case")
            expr_id = visit(node.expr)
            dot.edge(my_id, expr_id, label="sel")
            for item in node.items:
                item_id = visit(item)
                dot.edge(my_id, item_id)
            if node.default:
                default_id = next_id()
                dot.node(default_id, "default")
                for stmt in node.default:
                    child_id = visit(stmt)
                    dot.edge(default_id, child_id)
                dot.edge(my_id, default_id)
            return my_id

        elif isinstance(node, CaseItem):
            my_id = next_id()
            pattern_id = visit(node.pattern)
            dot.node(my_id, "item")
            dot.edge(my_id, pattern_id, label="match")
            for stmt in node.statements:
                stmt_id = visit(stmt)
                dot.edge(my_id, stmt_id, label="stmt")
            return my_id

        elif isinstance(node, list):
            # for block or top level list of statements
            block_id = next_id()
            dot.node(block_id, "block")
            for item in node:
                item_id = visit(item)
                dot.edge(block_id, item_id)
            return block_id
        
        elif isinstance(node, Module):
            my_id = next_id()
            dot.node(my_id, f"module\\n{node.name}")
            for item in node.items:
                item_id = visit(item)
                dot.edge(my_id, item_id)
            return my_id

        else:
            # fallback for unknowns
            my_id = next_id()
            dot.node(my_id, f"unknown: {type(node).__name__}")
            return my_id

    for top in ast:
        visit(top)

    return dot
