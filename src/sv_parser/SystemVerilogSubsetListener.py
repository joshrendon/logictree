# Generated from SystemVerilogSubset.g4 by ANTLR 4.13.1
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


    # Enter a parse tree produced by SystemVerilogSubsetParser#module_identifier.
    def enterModule_identifier(self, ctx:SystemVerilogSubsetParser.Module_identifierContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#module_identifier.
    def exitModule_identifier(self, ctx:SystemVerilogSubsetParser.Module_identifierContext):
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


    # Enter a parse tree produced by SystemVerilogSubsetParser#range.
    def enterRange(self, ctx:SystemVerilogSubsetParser.RangeContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#range.
    def exitRange(self, ctx:SystemVerilogSubsetParser.RangeContext):
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


    # Enter a parse tree produced by SystemVerilogSubsetParser#blocking_assignment.
    def enterBlocking_assignment(self, ctx:SystemVerilogSubsetParser.Blocking_assignmentContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#blocking_assignment.
    def exitBlocking_assignment(self, ctx:SystemVerilogSubsetParser.Blocking_assignmentContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#variable_lvalue.
    def enterVariable_lvalue(self, ctx:SystemVerilogSubsetParser.Variable_lvalueContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#variable_lvalue.
    def exitVariable_lvalue(self, ctx:SystemVerilogSubsetParser.Variable_lvalueContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#begin_end_block.
    def enterBegin_end_block(self, ctx:SystemVerilogSubsetParser.Begin_end_blockContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#begin_end_block.
    def exitBegin_end_block(self, ctx:SystemVerilogSubsetParser.Begin_end_blockContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#if_statement.
    def enterIf_statement(self, ctx:SystemVerilogSubsetParser.If_statementContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#if_statement.
    def exitIf_statement(self, ctx:SystemVerilogSubsetParser.If_statementContext):
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


    # Enter a parse tree produced by SystemVerilogSubsetParser#expression_list.
    def enterExpression_list(self, ctx:SystemVerilogSubsetParser.Expression_listContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#expression_list.
    def exitExpression_list(self, ctx:SystemVerilogSubsetParser.Expression_listContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#AndExpr.
    def enterAndExpr(self, ctx:SystemVerilogSubsetParser.AndExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#AndExpr.
    def exitAndExpr(self, ctx:SystemVerilogSubsetParser.AndExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#ConstExpr.
    def enterConstExpr(self, ctx:SystemVerilogSubsetParser.ConstExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#ConstExpr.
    def exitConstExpr(self, ctx:SystemVerilogSubsetParser.ConstExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#IdExpr.
    def enterIdExpr(self, ctx:SystemVerilogSubsetParser.IdExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#IdExpr.
    def exitIdExpr(self, ctx:SystemVerilogSubsetParser.IdExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#XorExpr.
    def enterXorExpr(self, ctx:SystemVerilogSubsetParser.XorExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#XorExpr.
    def exitXorExpr(self, ctx:SystemVerilogSubsetParser.XorExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#BitwiseNotExpr.
    def enterBitwiseNotExpr(self, ctx:SystemVerilogSubsetParser.BitwiseNotExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#BitwiseNotExpr.
    def exitBitwiseNotExpr(self, ctx:SystemVerilogSubsetParser.BitwiseNotExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#EqExpr.
    def enterEqExpr(self, ctx:SystemVerilogSubsetParser.EqExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#EqExpr.
    def exitEqExpr(self, ctx:SystemVerilogSubsetParser.EqExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#XnorExpr.
    def enterXnorExpr(self, ctx:SystemVerilogSubsetParser.XnorExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#XnorExpr.
    def exitXnorExpr(self, ctx:SystemVerilogSubsetParser.XnorExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#LogicalNotExpr.
    def enterLogicalNotExpr(self, ctx:SystemVerilogSubsetParser.LogicalNotExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#LogicalNotExpr.
    def exitLogicalNotExpr(self, ctx:SystemVerilogSubsetParser.LogicalNotExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#ParenExpr.
    def enterParenExpr(self, ctx:SystemVerilogSubsetParser.ParenExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#ParenExpr.
    def exitParenExpr(self, ctx:SystemVerilogSubsetParser.ParenExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#OrExpr.
    def enterOrExpr(self, ctx:SystemVerilogSubsetParser.OrExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#OrExpr.
    def exitOrExpr(self, ctx:SystemVerilogSubsetParser.OrExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#NegateExpr.
    def enterNegateExpr(self, ctx:SystemVerilogSubsetParser.NegateExprContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#NegateExpr.
    def exitNegateExpr(self, ctx:SystemVerilogSubsetParser.NegateExprContext):
        pass


    # Enter a parse tree produced by SystemVerilogSubsetParser#literal.
    def enterLiteral(self, ctx:SystemVerilogSubsetParser.LiteralContext):
        pass

    # Exit a parse tree produced by SystemVerilogSubsetParser#literal.
    def exitLiteral(self, ctx:SystemVerilogSubsetParser.LiteralContext):
        pass



del SystemVerilogSubsetParser