import logging

from logictree.nodes import control, gates, hole, ops
from logictree.nodes.ops.ops import LogicVar
from sv_parser.SystemVerilogSubsetParser import (
    AndExprContext,
    BitwiseNotExprContext,
    ConstExprContext,
    Continuous_assignContext,
    EqExprContext,
    IdExprContext,
    IdNode,
    If_statementContext,
    LogicalNotExprContext,
    NegateExprContext,
    Number,
    OrExprContext,
    ParenExprContext,
    XnorExprContext,
    XorExprContext,
)
from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor

log = logging.getLogger(__name__)


def BinaryOp(op, lhs, rhs):
    return ops.LogicOp(op, [lhs, rhs])


def UnaryOp(op, val):
    return ops.LogicOp(op, [val])


# This lives in visitor.py or a separate lowerer.py
def lower_expr_to_logic_tree(expr):
    if isinstance(expr, BinaryOp):
        lhs = lower_expr_to_logic_tree(expr.left)
        rhs = lower_expr_to_logic_tree(expr.right)
        return ops.LogicOp(expr.op.upper(), [lhs, rhs])
    elif isinstance(expr, UnaryOp):
        val = lower_expr_to_logic_tree(expr.operand)
        return ops.LogicOp(expr.op.upper(), [val])
    elif isinstance(expr, IdNode):
        return ops.LogicVar(expr.name)
    elif isinstance(expr, Number):
        return ops.LogicConst(str(expr.value))
    else:
        log.info(f"[lower_expr_to_logic_tree] Unhandled: {expr}")
        return hole.LogicHole("unhandled_expr")


def lower_stmt_to_logic_tree(stmt):
    if isinstance(stmt, Continuous_assignContext):
        lhs = stmt.Identifier().getText()
        rhs = lower_stmt_to_logic_tree(stmt.expression())
        # return lower_expr_to_logic_tree(stmt.source)
        return control.LogicAssign(lhs=lhs, rhs=rhs)
    elif isinstance(stmt, If_statementContext):
        cond = lower_expr_to_logic_tree(stmt.condition)
        then = lower_stmt_to_logic_tree(stmt.then_body)
        if stmt.else_body:
            elze = lower_stmt_to_logic_tree(stmt.else_body)
        else:
            elze = hole.LogicHole("missing_else")
        # return a 2:1 mux: (cond AND then) OR (~cond AND else)
        return ops.LogicOp(
            "OR",
            [
                ops.LogicOp("AND", [cond, then]),
                ops.LogicOp("AND", [ops.LogicOp("NOT", [cond]), elze]),
            ],
        )
    elif isinstance(stmt, ParenExprContext):
        expr = lower_stmt_to_logic_tree(stmt.expression())
        return expr
    elif isinstance(stmt, IdExprContext):
        name = stmt.getText()
        return LogicVar(name)
    elif isinstance(stmt, ConstExprContext):
        name = stmt.getText()
        return LogicVar(name)
    elif isinstance(stmt, EqExprContext):
        lhs = lower_stmt_to_logic_tree(stmt.expression(0))
        rhs = lower_stmt_to_logic_tree(stmt.expression(1))
        return ops.LogicOp("EQ", [lhs, rhs])
    elif isinstance(stmt, AndExprContext):
        lhs = lower_stmt_to_logic_tree(stmt.expression(0))
        rhs = lower_stmt_to_logic_tree(stmt.expression(1))
        return ops.LogicOp("AND", [lhs, rhs])
    elif isinstance(stmt, OrExprContext):
        lhs = lower_stmt_to_logic_tree(stmt.expression(0))
        rhs = lower_stmt_to_logic_tree(stmt.expression(1))
        return ops.LogicOp("OR", [lhs, rhs])
    elif isinstance(stmt, XorExprContext):
        lhs = lower_stmt_to_logic_tree(stmt.expression(0))
        rhs = lower_stmt_to_logic_tree(stmt.expression(1))
        return ops.LogicOp("XOR", [lhs, rhs])
    elif isinstance(stmt, XnorExprContext):
        lhs = lower_stmt_to_logic_tree(stmt.expression(0))
        rhs = lower_stmt_to_logic_tree(stmt.expression(1))
        return ops.LogicOp("XNOR", [lhs, rhs])
    elif isinstance(stmt, NegateExprContext):
        expr = lower_stmt_to_logic_tree(stmt.expression())
        return ops.LogicOp("NOT", [expr])
    elif isinstance(stmt, BitwiseNotExprContext):
        expr = lower_stmt_to_logic_tree(stmt.expression())
        return ops.LogicOp("NOT", [expr])
    elif isinstance(stmt, LogicalNotExprContext):
        expr = lower_stmt_to_logic_tree(stmt.expression())
        return ops.LogicOp("NOT", [expr])
    else:
        log.debug(" lower_stmt_to_logic_tree() class of stmt:", type(stmt).__name__)
        log.warning(f" [lower_stmt_to_logic_tree] Unhandled: {stmt.getText()}")
        return hole.LogicHole("unhandled_stmt")


def flatten_stmt(stmt):
    # If we have a list with one item, unwrap it
    if isinstance(stmt, list) and len(stmt) == 1:
        return stmt[0]
    return stmt


def simplify_xnor(lhs, rhs):
    """Simplify an XNOR expression if possible."""

    log.debug(" simplify_xnor() lhs:", lhs)
    log.debug("simplify_xnor() rhs:", rhs)

    # Case: XNOR(x, 1) => x
    # Case: XNOR(x, 0) => NOT(x)
    if isinstance(rhs, ops.LogicConst):
        if rhs.value == "1'b1":
            return lhs  # A == 1 -> A
        if rhs.value == "1'b0":
            return gates.NotOp(lhs)  # A == 0 -> ~A

    if isinstance(lhs, ops.LogicConst):
        if lhs.value == "1":
            return rhs
        if lhs.value == "0":
            return gates.NotOp(rhs)

    return ops.LogicOp("XNOR", [lhs, rhs])


class ASTBuilder(SystemVerilogSubsetVisitor):
    def genericVisit(self, ctx):
        rule_name = type(ctx).__name__
        text = ctx.getText()
        log.debug(f"[GENERIC VISIT] {rule_name}: {text}")
        return self.visitChildren(ctx)

    def visitCompilation_unit(self, ctx):
        return {"modules": [self.visit(mod) for mod in ctx.module_declaration()]}

    def visitModule_declaration(self, ctx):
        module_name = ctx.module_identifier().getText()
        ports = []
        items = []

        log.info("Visiting module:", module_name)

        for item in ctx.module_item():
            result = self.visit(item)
            if result:
                items.append(result)

        return {
            "type": "module",
            "name": module_name,
            "ports": ports,  # You can fill this in later
            "items": items,
        }

    def visitChildren(self, ctx):
        log.debug(f"[children] visiting children of {type(ctx).__name__}")
        return self.genericVisit(ctx)
        # return super().visitChildren(ctx)

    def visitModule_item(self, ctx):
        if ctx.always_comb_block():
            return self.visit(ctx.always_comb_block())
        # return {'type': 'unhandled', 'ctx': ctx}

    def visitAlways_comb_block(self, ctx):
        return self.visit(ctx.statement())

    def visitContinuous_assign(self, ctx):
        return {
            "type": "assign",
            "target": ctx.Identifier().getText(),
            "source": self.visit(ctx.expression()),
            "ctx": ctx,  # attach for lowering
        }

    def visitCase_statement(self, ctx):
        cond_expr = self.visit(ctx.expression())
        result = None

        for item in reversed(ctx.case_item()):
            log.debug(" visitCase_statement() dir(item)", dir(item))
            case_value_exprs = item.constant_expression()
            case_result_stmt = self.visit(item.statement())
            if case_value_exprs:
                conds = [
                    ops.LogicOp("EQ", [cond_expr, self.visit(expr)])
                    for expr in case_value_exprs
                ]
                total_cond = conds[0] if len(conds) == 1 else ops.LogicOp("OR", conds)
                result = ops.LogicOp(
                    "ITE", [total_cond, case_result_stmt, result or ops.LogicConst(0)]
                )
            else:
                # default
                result = case_result_stmt if result is None else result

        return result

    def visitCase_item(self, ctx):
        if ctx.DEFAULT():
            condition_expr = None
        else:
            condition_expr = self.visit(ctx.expression())

        stmt = self.visit(ctx.statement())
        return (condition_expr, stmt)

    def visitStatement_item(self, ctx):
        if ctx.case_statement():
            return self.visit(ctx.case_statement())
        if ctx.if_else_if_chain():
            return self.visit(ctx.if_else_if_chain())
        if ctx.non_blocking_assignment():
            return self.visit(ctx.non_blocking_assignment())
        if ctx.blocking_assignment():
            return self.visit(ctx.blocking_assignment())
        # You might also want to support begin-end blocks
        if ctx.statement():
            return self.visit(ctx.statement())
        return None

    def visitStatement(self, ctx):
        log.debug(" visitStatement() - ctx:", ctx.getText())
        # log.debug("DEBUG: visitStatement() dir(ctx):", dir(ctx))
        # log.debug("DEBUG: TREE:\n", ctx.toStringTree(recog=ctx.parser))
        if ctx.begin_end_block():
            log.debug(" visitStatement begin_end_block")
            return [self.visit(s) for s in ctx.begin_end_block().statement()]
        elif ctx.ifStatement():
            log.debug(" visitStatement ifStatement")
            return self.visit(ctx.ifStatement())
        elif ctx.case_statement():
            log.debug(" visitStatement case_statement")
            return self.visit(ctx.case_statement())
        elif ctx.getChildCount() >= 2 and ctx.getChild(0).getText() == "begin":
            log.debug(" visitStatement begin end block")
            # This is a begin-end block -> collect inner statements
            return [self.visit(stmt) for stmt in ctx.statement()]
        elif ctx.expression():
            log.debug(" visitStatement expression:", ctx.expression().getText())
            # Might be an assignment statement
            return self.visit(ctx.expression())
        else:
            log.error("ERROR Unhandled statement:\n", ctx.getText())
            return None

    def visitIf_statement(self, ctx):
        log.debug(" visitIf_statement()")
        cond_expr_ctx = ctx.expression()
        then_stmt_ctx = ctx.statement(0)
        log.debug("Condition:", cond_expr_ctx.getText())
        log.debug("Then branch:", then_stmt_ctx.getText())
        else_stmt_ctx = ctx.statement(1) if ctx.ELSE() else None
        log.debug("Else exists:", else_stmt_ctx.getText())
        log.debug("else_stmt_ctx:", else_stmt_ctx.toStringTree(recog=ctx.parser))

        if ctx.ELSE():
            log.debug("Else exists:", else_stmt_ctx.getText())

        cond_expr = self.visit(cond_expr_ctx)
        then_stmt = flatten_stmt(self.visit(then_stmt_ctx))
        else_stmt = flatten_stmt(self.visit(else_stmt_ctx)) if else_stmt_ctx else None

        return {
            "type": "if",
            "cond": cond_expr,
            "then": then_stmt,
            "else": else_stmt,
        }

    def visitAndExpr(self, ctx):
        left = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(0))
        if left is None or right is None:
            log.debug(" visitAndExpr with", ctx.getText())
        # return BinaryOp('AND', left, right)
        return ops.LogicOp("AND", [left, right])

    def visitOrExpr(self, ctx):
        log.debug(" visitOrExpr with", ctx.getText())
        # return BinaryOp('OR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))
        return ops.LogicOp(
            "OR", [self.visit(ctx.expression(0)), self.visit(ctx.expression(1))]
        )

    def visitXorExpr(self, ctx):
        log.debug(" visitXOrExpr with", ctx.getText())
        # return BinaryOp('XOR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))
        return ops.LogicOp(
            "XOR", [self.visit(ctx.expression(0)), self.visit(ctx.expression(1))]
        )

    def visitXnorExpr(self, ctx):
        log.debug(" visitXnorExpr with", ctx.getText())
        # return BinaryOp('XNOR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))
        return ops.LogicOp(
            "XNOR", [self.visit(ctx.expression(0)), self.visit(ctx.expression(1))]
        )

    def visitLogicalNotExpr(self, ctx):
        log.debug(" visitLogicalNotExpr with", ctx.getText())
        sub = self.visit(ctx.expression())
        if sub is None:
            log.debug(" visitLogicalNotExpr() got None for sub-expression")
        return UnaryOp("NOT", sub)

    def visitBitwiseNotExpr(self, ctx):
        log.debug(" visitBitwiseNotExpr with", ctx.getText())
        sub = self.visit(ctx.expression())
        if sub is None:
            log.debug(" visitBitwiseNotExpr() got None for sub-expression")
        return UnaryOp("NOT", sub)

    def visitNegateExpr(self, ctx):
        log.debug(" visitNegateExpr with", ctx.getText())
        sub = self.visit(ctx.expression())
        if sub is None:
            log.debug(" visitNegateExpr() got None for sub-expression")
        return UnaryOp("NOT", sub)  # or NEGATE if added to gate types

    def visitEqExpr(self, ctx):
        log.debug(" visitEqExpr with", ctx.getText())
        expr0 = self.visit(ctx.expression(0))
        expr1 = self.visit(ctx.expression(1))
        log.debug(" visitEqExpr raw expr0", expr0)
        log.debug(" visitEqExpr raw expr1", expr1)

        # simp_expr0 = simplify_xnor(expr0)
        # simp_expr1 = simplify_xnor(expr1)

        simplified = simplify_xnor(expr0, expr1)

        log.debug(" simplified XNOR:", simplified)
        return simplified

    def visitParenExpr(self, ctx):
        log.debug(" visitParenExpr with", ctx.getText())
        return self.visit(ctx.expression())

    def visitConstExpr(self, ctx):
        log.debug(" visitConstExpr with", ctx.getText())
        return hole.LogicHole(ctx.getText())

    def visitIdExpr(self, ctx):
        log.debug(" visitIdExpr with", ctx.getText())
        return hole.LogicHole(ctx.getText())
