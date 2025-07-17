# Visitor for AST
from logictree.nodes import LogicOp, LogicHole

def BinaryOp(op, lhs, rhs):
    return LogicOp(op, [lhs, rhs])

def UnaryOp(op, val):
    return LogicOp(op, [val])

from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor
from sv_parser.SystemVerilogSubsetParser import *

class ASTBuilder(SystemVerilogSubsetVisitor):
    def visitCompilation_unit(self, ctx):
        return {'modules': [self.visit(mod) for mod in ctx.module_declaration()]}

    def visitModule_declaration(self, ctx):
        return {
            'type': 'module',
            'name': ctx.Identifier().getText(),
            'ports': [],
            'items': [self.visit(item) for item in ctx.module_item()]
        }

    def visitModule_item(self, ctx):
        if ctx.continuous_assign():
            return self.visit(ctx.continuous_assign())
        return {'type': 'unhandled', 'ctx': ctx}

    def visitContinuous_assign(self, ctx):
        return {
            'type': 'assign',
            'target': ctx.Identifier().getText(),
            'source': self.visit(ctx.expression()),
            'ctx': ctx  # attach for lowering
        }

    def visitAndExpr(self, ctx):
        left  = self.visit(ctx.expression(0))
        right = self.visit(ctx.expression(0))
        if left is None or right is None:
            print("DEBUG: visitAndExpr with", ctx.getText())
        return BinaryOp('AND', left, right)

    def visitOrExpr(self, ctx):
        print("DEBUG: visitOrExpr with", ctx.getText())
        return BinaryOp('OR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))

    def visitXorExpr(self, ctx):
        print("DEBUG: visitXOrExpr with", ctx.getText())
        return BinaryOp('XOR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))

    def visitXnorExpr(self, ctx):
        print("DEBUG: visitXnorExpr with", ctx.getText())
        return BinaryOp('XNOR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))

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
        return BinaryOp('XNOR', self.visit(ctx.expression(0)), self.visit(ctx.expression(1)))

    def visitParenExpr(self, ctx):
        print("DEBUG: visitParenExpr with", ctx.getText())
        return self.visit(ctx.expression())

    def visitConstExpr(self, ctx):
        print("DEBUG: visitConstExpr with", ctx.getText())
        return LogicHole(ctx.getText())

    def visitIdExpr(self, ctx):
        print("DEBUG: visitIdExpr with", ctx.getText())
        return LogicHole(ctx.getText())

