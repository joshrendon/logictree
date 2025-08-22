# Generated from SimpleVerilogExpr.g4 by ANTLR 4.13.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,15,42,2,0,7,0,2,1,7,1,1,0,1,0,1,0,1,0,1,0,1,0,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,1,1,1,1,3,1,20,8,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,1,1,1,1,1,1,1,5,1,37,8,1,10,1,12,1,40,9,1,1,1,0,1,
        2,2,0,2,0,0,47,0,4,1,0,0,0,2,19,1,0,0,0,4,5,5,1,0,0,5,6,5,13,0,0,
        6,7,5,2,0,0,7,8,3,2,1,0,8,9,5,3,0,0,9,1,1,0,0,0,10,11,6,1,-1,0,11,
        12,5,8,0,0,12,20,3,2,1,5,13,14,5,10,0,0,14,15,3,2,1,0,15,16,5,11,
        0,0,16,20,1,0,0,0,17,20,5,12,0,0,18,20,5,13,0,0,19,10,1,0,0,0,19,
        13,1,0,0,0,19,17,1,0,0,0,19,18,1,0,0,0,20,38,1,0,0,0,21,22,10,9,
        0,0,22,23,5,4,0,0,23,37,3,2,1,10,24,25,10,8,0,0,25,26,5,5,0,0,26,
        37,3,2,1,9,27,28,10,7,0,0,28,29,5,6,0,0,29,37,3,2,1,8,30,31,10,6,
        0,0,31,32,5,7,0,0,32,37,3,2,1,7,33,34,10,4,0,0,34,35,5,9,0,0,35,
        37,3,2,1,5,36,21,1,0,0,0,36,24,1,0,0,0,36,27,1,0,0,0,36,30,1,0,0,
        0,36,33,1,0,0,0,37,40,1,0,0,0,38,36,1,0,0,0,38,39,1,0,0,0,39,3,1,
        0,0,0,40,38,1,0,0,0,3,19,36,38
    ]

class SimpleVerilogExprParser ( Parser ):

    grammarFileName = "SimpleVerilogExpr.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'assign'", "'='", "';'", "'&'", "'|'", 
                     "'^'", "'~^'", "'~'", "'=='", "'('", "')'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "BITCONST", "IDENT", "DEC_NUMBER", "WS" ]

    RULE_assign_stmt = 0
    RULE_expr = 1

    ruleNames =  [ "assign_stmt", "expr" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    T__8=9
    T__9=10
    T__10=11
    BITCONST=12
    IDENT=13
    DEC_NUMBER=14
    WS=15

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class Assign_stmtContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return SimpleVerilogExprParser.RULE_assign_stmt

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)



    class AssignStatementContext(Assign_stmtContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.Assign_stmtContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def IDENT(self):
            return self.getToken(SimpleVerilogExprParser.IDENT, 0)
        def expr(self):
            return self.getTypedRuleContext(SimpleVerilogExprParser.ExprContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAssignStatement" ):
                listener.enterAssignStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAssignStatement" ):
                listener.exitAssignStatement(self)



    def assign_stmt(self):

        localctx = SimpleVerilogExprParser.Assign_stmtContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_assign_stmt)
        try:
            localctx = SimpleVerilogExprParser.AssignStatementContext(self, localctx)
            self.enterOuterAlt(localctx, 1)
            self.state = 4
            self.match(SimpleVerilogExprParser.T__0)
            self.state = 5
            self.match(SimpleVerilogExprParser.IDENT)
            self.state = 6
            self.match(SimpleVerilogExprParser.T__1)
            self.state = 7
            self.expr(0)
            self.state = 8
            self.match(SimpleVerilogExprParser.T__2)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExprContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return SimpleVerilogExprParser.RULE_expr

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class AndExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SimpleVerilogExprParser.ExprContext)
            else:
                return self.getTypedRuleContext(SimpleVerilogExprParser.ExprContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAndExpr" ):
                listener.enterAndExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAndExpr" ):
                listener.exitAndExpr(self)


    class ConstExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def BITCONST(self):
            return self.getToken(SimpleVerilogExprParser.BITCONST, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConstExpr" ):
                listener.enterConstExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConstExpr" ):
                listener.exitConstExpr(self)


    class IdExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def IDENT(self):
            return self.getToken(SimpleVerilogExprParser.IDENT, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIdExpr" ):
                listener.enterIdExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIdExpr" ):
                listener.exitIdExpr(self)


    class XorExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SimpleVerilogExprParser.ExprContext)
            else:
                return self.getTypedRuleContext(SimpleVerilogExprParser.ExprContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterXorExpr" ):
                listener.enterXorExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitXorExpr" ):
                listener.exitXorExpr(self)


    class EqExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SimpleVerilogExprParser.ExprContext)
            else:
                return self.getTypedRuleContext(SimpleVerilogExprParser.ExprContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEqExpr" ):
                listener.enterEqExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEqExpr" ):
                listener.exitEqExpr(self)


    class XnorExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SimpleVerilogExprParser.ExprContext)
            else:
                return self.getTypedRuleContext(SimpleVerilogExprParser.ExprContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterXnorExpr" ):
                listener.enterXnorExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitXnorExpr" ):
                listener.exitXnorExpr(self)


    class NotExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self):
            return self.getTypedRuleContext(SimpleVerilogExprParser.ExprContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNotExpr" ):
                listener.enterNotExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNotExpr" ):
                listener.exitNotExpr(self)


    class ParenExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self):
            return self.getTypedRuleContext(SimpleVerilogExprParser.ExprContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParenExpr" ):
                listener.enterParenExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParenExpr" ):
                listener.exitParenExpr(self)


    class OrExprContext(ExprContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SimpleVerilogExprParser.ExprContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def expr(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SimpleVerilogExprParser.ExprContext)
            else:
                return self.getTypedRuleContext(SimpleVerilogExprParser.ExprContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOrExpr" ):
                listener.enterOrExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOrExpr" ):
                listener.exitOrExpr(self)



    def expr(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = SimpleVerilogExprParser.ExprContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 2
        self.enterRecursionRule(localctx, 2, self.RULE_expr, _p)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 19
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [8]:
                localctx = SimpleVerilogExprParser.NotExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 11
                self.match(SimpleVerilogExprParser.T__7)
                self.state = 12
                self.expr(5)
                pass
            elif token in [10]:
                localctx = SimpleVerilogExprParser.ParenExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 13
                self.match(SimpleVerilogExprParser.T__9)
                self.state = 14
                self.expr(0)
                self.state = 15
                self.match(SimpleVerilogExprParser.T__10)
                pass
            elif token in [12]:
                localctx = SimpleVerilogExprParser.ConstExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 17
                self.match(SimpleVerilogExprParser.BITCONST)
                pass
            elif token in [13]:
                localctx = SimpleVerilogExprParser.IdExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 18
                self.match(SimpleVerilogExprParser.IDENT)
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 38
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,2,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 36
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,1,self._ctx)
                    if la_ == 1:
                        localctx = SimpleVerilogExprParser.AndExprContext(self, SimpleVerilogExprParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 21
                        if not self.precpred(self._ctx, 9):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 9)")
                        self.state = 22
                        self.match(SimpleVerilogExprParser.T__3)
                        self.state = 23
                        self.expr(10)
                        pass

                    elif la_ == 2:
                        localctx = SimpleVerilogExprParser.OrExprContext(self, SimpleVerilogExprParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 24
                        if not self.precpred(self._ctx, 8):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 8)")
                        self.state = 25
                        self.match(SimpleVerilogExprParser.T__4)
                        self.state = 26
                        self.expr(9)
                        pass

                    elif la_ == 3:
                        localctx = SimpleVerilogExprParser.XorExprContext(self, SimpleVerilogExprParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 27
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 28
                        self.match(SimpleVerilogExprParser.T__5)
                        self.state = 29
                        self.expr(8)
                        pass

                    elif la_ == 4:
                        localctx = SimpleVerilogExprParser.XnorExprContext(self, SimpleVerilogExprParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 30
                        if not self.precpred(self._ctx, 6):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 6)")
                        self.state = 31
                        self.match(SimpleVerilogExprParser.T__6)
                        self.state = 32
                        self.expr(7)
                        pass

                    elif la_ == 5:
                        localctx = SimpleVerilogExprParser.EqExprContext(self, SimpleVerilogExprParser.ExprContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expr)
                        self.state = 33
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")
                        self.state = 34
                        self.match(SimpleVerilogExprParser.T__8)
                        self.state = 35
                        self.expr(5)
                        pass

             
                self.state = 40
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,2,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[1] = self.expr_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def expr_sempred(self, localctx:ExprContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 9)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 8)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 7)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 6)
         

            if predIndex == 4:
                return self.precpred(self._ctx, 4)
         




