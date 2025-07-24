# Visitor for AST
from logictree.nodes import LogicOp, LogicHole, LogicConst, LogicHole, NotOp

def BinaryOp(op, lhs, rhs):
    return LogicOp(op, [lhs, rhs])

def UnaryOp(op, val):
    return LogicOp(op, [val])

# This lives in visitor.py or a separate lowerer.py
def lower_expr_to_logic_tree(expr):
    if isinstance(expr, BinaryOp):
        lhs = lower_expr_to_logic_tree(expr.left)
        rhs = lower_expr_to_logic_tree(expr.right)
        return LogicOp(expr.op.upper(), [lhs, rhs])
    elif isinstance(expr, UnaryOp):
        val = lower_expr_to_logic_tree(expr.operand)
        return LogicOp(expr.op.upper(), [val])
    elif isinstance(expr, IdNode):
        return LogicVar(expr.name)
    elif isinstance(expr, Number):
        return LogicConst(str(expr.value))
    else:
        print(f"[lower_expr_to_logic_tree] Unhandled: {expr}")
        return LogicHole("unhandled_expr")

def lower_stmt_to_logic_tree(stmt):
    if isinstance(stmt, AssignStmtCtxtClass):
        return lower_expr_to_logic_tree(stmt.source)
    elif isinstance(stmt, IfStatement):
        cond = lower_expr_to_logic_tree(stmt.condition)
        then = lower_stmt_to_logic_tree(stmt.then_body)
        if stmt.else_body:
            elze = lower_stmt_to_logic_tree(stmt.else_body)
        else:
            elze = LogicHole("missing_else")
        # return a 2:1 mux: (cond AND then) OR (~cond AND else)
        return LogicOp("OR", [
            LogicOp("AND", [cond, then]),
            LogicOp("AND", [LogicOp("NOT", [cond]), elze])
        ])
    else:
        print(f"[lower_stmt_to_logic_tree] Unhandled: {stmt}")
        return LogicHole("unhandled_stmt")

def flatten_stmt(stmt):
    # If we have a list with one item, unwrap it
    if isinstance(stmt, list) and len(stmt) == 1:
        return stmt[0]
    return stmt

def simplify_xnor(lhs, rhs):
    """Simplify an XNOR expression if possible."""

    print("DEBUG: simplify_xnor() lhs:", lhs)
    print("DEBUG: simplify_xnor() rhs:", rhs)

    # Case: XNOR(x, 1) => x
    # Case: XNOR(x, 0) => NOT(x)
    if isinstance(rhs, LogicConst):
        if rhs.value == "1'b1":
            return lhs # A == 1 -> A
        if rhs.value == "1'b0":
            return NotOp(lhs)  # A == 0 -> ~A

    if isinstance(lhs, LogicConst):
        if lhs.value == "1":
            return rhs
        if lhs.value == "0":
            return NotOp(rhs)

    return LogicOp('XNOR', [lhs, rhs])

#def simplify_xnor(expr):

    #print("DEBUG: simplify_xnor() expr:", dir(expr))
    #if isinstance(expr, LogicOp) and expr.op == 'XNOR':
    #    a, b = expr.args
    #    if isinstance(b, LogicConst):
    #        if b.value in ('1', "1'b1"): # Normalize this format if needed
    #            return a
    #        elif b.value in ('0', "1'b0"):
    #            return LogicOp('NOT', [a])
    #return expr

from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor
from sv_parser.SystemVerilogSubsetParser import *

class ASTBuilder(SystemVerilogSubsetVisitor):
    def visitCompilation_unit(self, ctx):
        return {'modules': [self.visit(mod) for mod in ctx.module_declaration()]}

    def visitModule_declaration(self, ctx):
        module_name = ctx.module_identifier().getText()
        ports = []
        items = []
    
        print("Visiting module:", module_name)

        for item in ctx.module_item():
            result = self.visit(item)
            if result:
                items.append(result)
    
        return {
            "type": "module",
            "name": module_name,
            "ports": ports,  # You can fill this in later
            "items": items
        }

    def visitModule_item(self, ctx):
        if ctx.always_comb_block():
            return self.visit(ctx.always_comb_block())
        #return {'type': 'unhandled', 'ctx': ctx}

    def visitAlways_comb_block(self, ctx):
        return self.visit(ctx.statement())

    def visitContinuous_assign(self, ctx):
        return {
            'type': 'assign',
            'target': ctx.Identifier().getText(),
            'source': self.visit(ctx.expression()),
            'ctx': ctx  # attach for lowering
        }

    def visitCase_statement(self, ctx):
        cond_expr = self.visit(ctx.expression())
        result = None
    
        for item in reversed(ctx.case_item()):
            print("DEBUG: visitCase_statement() dir(item)", dir(item))
            case_value_exprs = item.constant_expression()
            case_result_stmt = self.visit(item.statement())
            if case_value_exprs:
                conds = [LogicOp("EQ", [cond_expr, self.visit(expr)]) for expr in case_value_exprs]
                total_cond = conds[0] if len(conds) == 1 else LogicOp("OR", conds)
                result = LogicOp("ITE", [total_cond, case_result_stmt, result or LogicConst(0)])
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
        print("DEBUG: visitStatement() - ctx:", ctx.getText())
        #print("DEBUG: visitStatement() dir(ctx):", dir(ctx))
        #print("DEBUG: TREE:\n", ctx.toStringTree(recog=ctx.parser))
        if ctx.begin_end_block():
            print("DEBUG: visitStatement begin_end_block")
            return [self.visit(s) for s in ctx.begin_end_block().statement()]
        elif ctx.ifStatement():
            print("DEBUG: visitStatement ifStatement")
            return self.visit(ctx.ifStatement())
        elif ctx.case_statement():
            print("DEBUG: visitStatement case_statement")
            return self.visit(ctx.case_statement())
        elif ctx.getChildCount() >= 2 and ctx.getChild(0).getText() == "begin":
            print("DEBUG: visitStatement begin end block")
            # This is a begin-end block -> collect inner statements
            return [self.visit(stmt) for stmt in ctx.statement()]
        elif ctx.expression():
            print("DEBUG: visitStatement expression:", ctx.expression().getText())
            # Might be an assignment statement
            return self.visit(ctx.expression())
        else:
            print("Error Unhandled statement:\n", ctx.getText())
            return None

    def visitContinuous_assign(self, ctx):
        lhs = ctx.Identifier().getText()
        rhs = self.visit(ctx.expression())
        return {
           "type": "assign",
           "target": lhs,
           "value": rhs,
        }
    
    def visitIfStatement(self, ctx):
        print("DEBUG: visitIfStatement()")
        cond_expr_ctx = ctx.expression()
        then_stmt_ctx = ctx.statement(0)
        print("Condition:",   cond_expr_ctx.getText())
        print("Then branch:", then_stmt_ctx.getText())
        else_stmt_ctx = ctx.statement(1) if ctx.ELSE() else None
        print("Else exists:", else_stmt_ctx.getText())
        print("else_stmt_ctx:", else_stmt_ctx.toStringTree(recog=ctx.parser))

        if ctx.ELSE():
            print("Else exists:", else_stmt_ctx.getText())

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
        left  = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(0))
        if left is None or right is None:
            print("DEBUG: visitAndExpr with", ctx.getText())
        #return BinaryOp('AND', left, right)
        return LogicOp('AND', [left, right])

    def visitOrExpr(self, ctx):
        print("DEBUG: visitOrExpr with", ctx.getText())
        #return BinaryOp('OR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))
        return LogicOp('OR', [self.visit(ctx.expression(0)), self.visit(ctx.expression(1))])

    def visitXorExpr(self, ctx):
        print("DEBUG: visitXOrExpr with", ctx.getText())
        #return BinaryOp('XOR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))
        return LogicOp('XOR', [self.visit(ctx.expression(0)), self.visit(ctx.expression(1))])

    def visitXnorExpr(self, ctx):
        print("DEBUG: visitXnorExpr with", ctx.getText())
        #return BinaryOp('XNOR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))
        return LogicOp('XNOR', [self.visit(ctx.expression(0)), self.visit(ctx.expression(1))])

    def visitLogicalNotExpr(self, ctx):
        print("DEBUG: visitLogicalNotExpr with", ctx.getText())
        sub = self.visit(ctx.expression())
        if sub is None:
            print("DEBUG: visitLogicalNotExpr() got None for sub-expression")
        return UnaryOp('NOT', sub)

    def visitBitwiseNotExpr(self, ctx):
        print("DEBUG: visitBitwiseNotExpr with", ctx.getText())
        sub = self.visit(ctx.expression())
        if sub is None:
            print("DEBUG: visitBitwiseNotExpr() got None for sub-expression")
        return UnaryOp('NOT', sub)

    def visitNegateExpr(self, ctx):
        print("DEBUG: visitNegateExpr with", ctx.getText())
        sub = self.visit(ctx.expression())
        if sub is None:
            print("DEBUG: visitNegateExpr() got None for sub-expression")
        return UnaryOp('NOT', sub) # or NEGATE if added to gate types

    def visitEqExpr(self, ctx):
        print("DEBUG: visitEqExpr with", ctx.getText())
        expr0 = self.visit(ctx.expression(0))
        expr1 = self.visit(ctx.expression(1))
        print("DEBUG: visitEqExpr raw expr0", expr0)
        print("DEBUG: visitEqExpr raw expr1", expr1)

        #simp_expr0 = simplify_xnor(expr0)
        #simp_expr1 = simplify_xnor(expr1)
        #print("DEBUG: visitEqExpr simp_expr0", simp_expr0)
        #print("DEBUG: visitEqExpr simp_expr1", simp_expr1)
        
        simplified = simplify_xnor(expr0, expr1)

        print("DEBUG: simplified XNOR:", simplified)
        return simplified
        #return BinaryOp('XNOR', simp_expr0, simp_expr1)

    def visitParenExpr(self, ctx):
        print("DEBUG: visitParenExpr with", ctx.getText())
        return self.visit(ctx.expression())

    def visitConstExpr(self, ctx):
        print("DEBUG: visitConstExpr with", ctx.getText())
        return LogicHole(ctx.getText())

    def visitIdExpr(self, ctx):
        print("DEBUG: visitIdExpr with", ctx.getText())
        return LogicHole(ctx.getText())



