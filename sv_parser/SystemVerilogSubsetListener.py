# Generated from SystemVerilogSubset.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .SystemVerilogSubsetParser import SystemVerilogSubsetParser
else:
    from SystemVerilogSubsetParser import SystemVerilogSubsetParser

# This class defines a complete listener for a parse tree produced by SystemVerilogSubsetParser.
class SystemVerilogSubsetListener(ParseTreeListener):

    # Enter a parse tree produced by SystemVerilogSubsetParser#compilation_unit.
    def enterCompilation_unit(self, ctx:SystemVerilogSubsetParser.Compilation_unitContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#compilation_unit.
    def exitCompilation_unit(self, ctx:SystemVerilogSubsetParser.Compilation_unitContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#module_declaration.
    def enterModule_declaration(self, ctx:SystemVerilogSubsetParser.Module_declarationContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#module_declaration.
    def exitModule_declaration(self, ctx:SystemVerilogSubsetParser.Module_declarationContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#port_list.
    def enterPort_list(self, ctx:SystemVerilogSubsetParser.Port_listContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#port_list.
    def exitPort_list(self, ctx:SystemVerilogSubsetParser.Port_listContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#port.
    def enterPort(self, ctx:SystemVerilogSubsetParser.PortContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#port.
    def exitPort(self, ctx:SystemVerilogSubsetParser.PortContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#data_type.
    def enterData_type(self, ctx:SystemVerilogSubsetParser.Data_typeContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#data_type.
    def exitData_type(self, ctx:SystemVerilogSubsetParser.Data_typeContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#module_item.
    def enterModule_item(self, ctx:SystemVerilogSubsetParser.Module_itemContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#module_item.
    def exitModule_item(self, ctx:SystemVerilogSubsetParser.Module_itemContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#net_declaration.
    def enterNet_declaration(self, ctx:SystemVerilogSubsetParser.Net_declarationContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#net_declaration.
    def exitNet_declaration(self, ctx:SystemVerilogSubsetParser.Net_declarationContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#continuous_assign.
    def enterContinuous_assign(self, ctx:SystemVerilogSubsetParser.Continuous_assignContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#continuous_assign.
    def exitContinuous_assign(self, ctx:SystemVerilogSubsetParser.Continuous_assignContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#always_comb_block.
    def enterAlways_comb_block(self, ctx:SystemVerilogSubsetParser.Always_comb_blockContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#always_comb_block.
    def exitAlways_comb_block(self, ctx:SystemVerilogSubsetParser.Always_comb_blockContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#statement.
    def enterStatement(self, ctx:SystemVerilogSubsetParser.StatementContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#statement.
    def exitStatement(self, ctx:SystemVerilogSubsetParser.StatementContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#case_statement.
    def enterCase_statement(self, ctx:SystemVerilogSubsetParser.Case_statementContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#case_statement.
    def exitCase_statement(self, ctx:SystemVerilogSubsetParser.Case_statementContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#case_item.
    def enterCase_item(self, ctx:SystemVerilogSubsetParser.Case_itemContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#case_item.
    def exitCase_item(self, ctx:SystemVerilogSubsetParser.Case_itemContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#default_item.
    def enterDefault_item(self, ctx:SystemVerilogSubsetParser.Default_itemContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#default_item.
    def exitDefault_item(self, ctx:SystemVerilogSubsetParser.Default_itemContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#expression.
    def enterExpression(self, ctx:SystemVerilogSubsetParser.ExpressionContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#expression.
    def exitExpression(self, ctx:SystemVerilogSubsetParser.ExpressionContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#OrExpr.
    def enterOrExpr(self, ctx:SystemVerilogSubsetParser.OrExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#OrExpr.
    def exitOrExpr(self, ctx:SystemVerilogSubsetParser.OrExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#OrPass.
    def enterOrPass(self, ctx:SystemVerilogSubsetParser.OrPassContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#OrPass.
    def exitOrPass(self, ctx:SystemVerilogSubsetParser.OrPassContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#XorExpr.
    def enterXorExpr(self, ctx:SystemVerilogSubsetParser.XorExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#XorExpr.
    def exitXorExpr(self, ctx:SystemVerilogSubsetParser.XorExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#XorPass.
    def enterXorPass(self, ctx:SystemVerilogSubsetParser.XorPassContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#XorPass.
    def exitXorPass(self, ctx:SystemVerilogSubsetParser.XorPassContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#AndExpr.
    def enterAndExpr(self, ctx:SystemVerilogSubsetParser.AndExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#AndExpr.
    def exitAndExpr(self, ctx:SystemVerilogSubsetParser.AndExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#AndPass.
    def enterAndPass(self, ctx:SystemVerilogSubsetParser.AndPassContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#AndPass.
    def exitAndPass(self, ctx:SystemVerilogSubsetParser.AndPassContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#NotExpr.
    def enterNotExpr(self, ctx:SystemVerilogSubsetParser.NotExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#NotExpr.
    def exitNotExpr(self, ctx:SystemVerilogSubsetParser.NotExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#BitNotExpr.
    def enterBitNotExpr(self, ctx:SystemVerilogSubsetParser.BitNotExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#BitNotExpr.
    def exitBitNotExpr(self, ctx:SystemVerilogSubsetParser.BitNotExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#NegateExpr.
    def enterNegateExpr(self, ctx:SystemVerilogSubsetParser.NegateExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#NegateExpr.
    def exitNegateExpr(self, ctx:SystemVerilogSubsetParser.NegateExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#PrimaryPass.
    def enterPrimaryPass(self, ctx:SystemVerilogSubsetParser.PrimaryPassContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#PrimaryPass.
    def exitPrimaryPass(self, ctx:SystemVerilogSubsetParser.PrimaryPassContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#IdExpr.
    def enterIdExpr(self, ctx:SystemVerilogSubsetParser.IdExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#IdExpr.
    def exitIdExpr(self, ctx:SystemVerilogSubsetParser.IdExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#NumExpr.
    def enterNumExpr(self, ctx:SystemVerilogSubsetParser.NumExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#NumExpr.
    def exitNumExpr(self, ctx:SystemVerilogSubsetParser.NumExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#ParenExpr.
    def enterParenExpr(self, ctx:SystemVerilogSubsetParser.ParenExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#ParenExpr.
    def exitParenExpr(self, ctx:SystemVerilogSubsetParser.ParenExprContext):
        pass



del SystemVerilogSubsetParser