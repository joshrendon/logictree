# Generated from SimpleVerilogExpr.g4 by ANTLR 4.13.2

from antlr4 import *

if "." in __name__:
    from .SimpleVerilogExprParser import SimpleVerilogExprParser
else:
    from SimpleVerilogExprParser import SimpleVerilogExprParser

# This class defines a complete listener for a parse tree produced by SimpleVerilogExprParser.
class SimpleVerilogExprListener(ParseTreeListener):

    # Enter a parse tree produced by SimpleVerilogExprParser#AssignStatement.
    def enterAssignStatement(self, ctx:SimpleVerilogExprParser.AssignStatementContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#AssignStatement.
    def exitAssignStatement(self, ctx:SimpleVerilogExprParser.AssignStatementContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#AndExpr.
    def enterAndExpr(self, ctx:SimpleVerilogExprParser.AndExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#AndExpr.
    def exitAndExpr(self, ctx:SimpleVerilogExprParser.AndExprContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#ConstExpr.
    def enterConstExpr(self, ctx:SimpleVerilogExprParser.ConstExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#ConstExpr.
    def exitConstExpr(self, ctx:SimpleVerilogExprParser.ConstExprContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#IdExpr.
    def enterIdExpr(self, ctx:SimpleVerilogExprParser.IdExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#IdExpr.
    def exitIdExpr(self, ctx:SimpleVerilogExprParser.IdExprContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#XorExpr.
    def enterXorExpr(self, ctx:SimpleVerilogExprParser.XorExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#XorExpr.
    def exitXorExpr(self, ctx:SimpleVerilogExprParser.XorExprContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#EqExpr.
    def enterEqExpr(self, ctx:SimpleVerilogExprParser.EqExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#EqExpr.
    def exitEqExpr(self, ctx:SimpleVerilogExprParser.EqExprContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#XnorExpr.
    def enterXnorExpr(self, ctx:SimpleVerilogExprParser.XnorExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#XnorExpr.
    def exitXnorExpr(self, ctx:SimpleVerilogExprParser.XnorExprContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#NotExpr.
    def enterNotExpr(self, ctx:SimpleVerilogExprParser.NotExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#NotExpr.
    def exitNotExpr(self, ctx:SimpleVerilogExprParser.NotExprContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#ParenExpr.
    def enterParenExpr(self, ctx:SimpleVerilogExprParser.ParenExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#ParenExpr.
    def exitParenExpr(self, ctx:SimpleVerilogExprParser.ParenExprContext):
        pass


    # Enter a parse tree produced by SimpleVerilogExprParser#OrExpr.
    def enterOrExpr(self, ctx:SimpleVerilogExprParser.OrExprContext):
        pass

    # Exit a parse tree produced by SimpleVerilogExprParser#OrExpr.
    def exitOrExpr(self, ctx:SimpleVerilogExprParser.OrExprContext):
        pass



del SimpleVerilogExprParser
