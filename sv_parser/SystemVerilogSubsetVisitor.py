# Generated from SystemVerilogSubset.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .SystemVerilogSubsetParser import SystemVerilogSubsetParser
else:
    from SystemVerilogSubsetParser import SystemVerilogSubsetParser

# This class defines a complete generic visitor for a parse tree produced by SystemVerilogSubsetParser.

class SystemVerilogSubsetVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SystemVerilogSubsetParser#compilation_unit.
    def visitCompilation_unit(self, ctx:SystemVerilogSubsetParser.Compilation_unitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#module_declaration.
    def visitModule_declaration(self, ctx:SystemVerilogSubsetParser.Module_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#module_identifier.
    def visitModule_identifier(self, ctx:SystemVerilogSubsetParser.Module_identifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#port_list.
    def visitPort_list(self, ctx:SystemVerilogSubsetParser.Port_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#port.
    def visitPort(self, ctx:SystemVerilogSubsetParser.PortContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#range.
    def visitRange(self, ctx:SystemVerilogSubsetParser.RangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#data_type.
    def visitData_type(self, ctx:SystemVerilogSubsetParser.Data_typeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#module_item.
    def visitModule_item(self, ctx:SystemVerilogSubsetParser.Module_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#net_declaration.
    def visitNet_declaration(self, ctx:SystemVerilogSubsetParser.Net_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#continuous_assign.
    def visitContinuous_assign(self, ctx:SystemVerilogSubsetParser.Continuous_assignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#always_comb_block.
    def visitAlways_comb_block(self, ctx:SystemVerilogSubsetParser.Always_comb_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#statement.
    def visitStatement(self, ctx:SystemVerilogSubsetParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#begin_end_block.
    def visitBegin_end_block(self, ctx:SystemVerilogSubsetParser.Begin_end_blockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#ifStatement.
    def visitIfStatement(self, ctx:SystemVerilogSubsetParser.IfStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#case_statement.
    def visitCase_statement(self, ctx:SystemVerilogSubsetParser.Case_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#case_item.
    def visitCase_item(self, ctx:SystemVerilogSubsetParser.Case_itemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#AndExpr.
    def visitAndExpr(self, ctx:SystemVerilogSubsetParser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#ConstExpr.
    def visitConstExpr(self, ctx:SystemVerilogSubsetParser.ConstExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#IdExpr.
    def visitIdExpr(self, ctx:SystemVerilogSubsetParser.IdExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#XorExpr.
    def visitXorExpr(self, ctx:SystemVerilogSubsetParser.XorExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#BitwiseNotExpr.
    def visitBitwiseNotExpr(self, ctx:SystemVerilogSubsetParser.BitwiseNotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#EqExpr.
    def visitEqExpr(self, ctx:SystemVerilogSubsetParser.EqExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#XnorExpr.
    def visitXnorExpr(self, ctx:SystemVerilogSubsetParser.XnorExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#LogicalNotExpr.
    def visitLogicalNotExpr(self, ctx:SystemVerilogSubsetParser.LogicalNotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#ParenExpr.
    def visitParenExpr(self, ctx:SystemVerilogSubsetParser.ParenExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#OrExpr.
    def visitOrExpr(self, ctx:SystemVerilogSubsetParser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#NegateExpr.
    def visitNegateExpr(self, ctx:SystemVerilogSubsetParser.NegateExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SystemVerilogSubsetParser#literal.
    def visitLiteral(self, ctx:SystemVerilogSubsetParser.LiteralContext):
        return self.visitChildren(ctx)



del SystemVerilogSubsetParser