from sv_parser.ast_nodes import (
    IdNode, Number, BinaryOp, UnaryOp, Assign,
    CaseStatement, CaseItem
)
from sv_parser.SystemVerilogSubsetVisitor import SystemVerilogSubsetVisitor

class ASTBuilder(SystemVerilogSubsetVisitor):
    def visitCompilation_unit(self, ctx):
        return [self.visit(mod) for mod in ctx.module_declaration()]

    def visitModule_declaration(self, ctx):
        name = ctx.Identifier().getText()
        ports = []
        if ctx.port_list():
            ports = [p.Identifier().getText() for p in ctx.port_list().port()]
        items = [self.visit(item) for item in ctx.module_item()]
        from sv_parser.ast_nodes import Module
        return Module(name=name, ports=ports, items=items)
        #return type('Module', (object,), {
        #    'name': name, 'ports': ports, 'items': items
        #})()

    def visitNet_declaration(self, ctx):
        return None

    def visitContinuous_assign(self, ctx):
        return Assign(target=ctx.Identifier().getText(), source=self.visit(ctx.expression()))

    def visitAlways_comb_block(self, ctx):
        return self.visit(ctx.statement())

    def visitStatement(self, ctx):
        if ctx.getChildCount() == 1:
            return self.visit(ctx.getChild(0))  # block or case
        if ctx.getChildCount() == 4 and ctx.getChild(1).getText() == '=':
            return Assign(target=ctx.Identifier().getText(), source=self.visit(ctx.expression()))
        return [self.visit(child) for child in ctx.statement()]  # compound block

    def visitCase_statement(self, ctx):
        expr = self.visit(ctx.expression())
        items = [self.visit(item) for item in ctx.case_item()]
        default = self.visit(ctx.default_item()) if ctx.default_item() else None
        return CaseStatement(expr=expr, items=items, default=default)

    def visitCase_item(self, ctx):
        pattern = self.visit(ctx.expression())
        stmt = self.visit(ctx.statement())
        return CaseItem(pattern=pattern, statements=[stmt] if not isinstance(stmt, list) else stmt)

    def visitDefault_item(self, ctx):
        stmt = self.visit(ctx.statement())
        return [stmt] if not isinstance(stmt, list) else stmt

    def visitOrExpr(self, ctx):
        return BinaryOp('|', self.visit(ctx.logical_or_expression()), self.visit(ctx.logical_xor_expression()))

    def visitOrPass(self, ctx):
        return self.visit(ctx.logical_xor_expression())

    def visitXorExpr(self, ctx):
        return BinaryOp('^', self.visit(ctx.logical_xor_expression()), self.visit(ctx.logical_and_expression()))

    def visitXorPass(self, ctx):
        return self.visit(ctx.logical_and_expression())

    def visitAndExpr(self, ctx):
        return BinaryOp('&', self.visit(ctx.logical_and_expression()), self.visit(ctx.unary_expression()))

    def visitAndPass(self, ctx):
        return self.visit(ctx.unary_expression())

    def visitNotExpr(self, ctx):
        return UnaryOp('!', self.visit(ctx.unary_expression()))

    def visitBitNotExpr(self, ctx):
        return UnaryOp('~', self.visit(ctx.unary_expression()))

    def visitNegateExpr(self, ctx):
        return UnaryOp('-', self.visit(ctx.unary_expression()))

    def visitPrimaryPass(self, ctx):
        return self.visit(ctx.primary_expression())

    def visitParenExpr(self, ctx):
        return self.visit(ctx.expression())

    def visitIdExpr(self, ctx):
        return IdNode(ctx.Identifier().getText())

    def visitNumExpr(self, ctx):
        return Number(int(ctx.Number().getText()))
