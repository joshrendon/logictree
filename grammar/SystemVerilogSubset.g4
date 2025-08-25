
grammar SystemVerilogSubset;

COLON: ':' ;
COMMA: ',' ;
SEMICOLON: ';' ;
ASSIGN: '=' ;
DEFAULT: 'default' ;
CASE: 'case' ;
ENDCASE: 'endcase' ;
BEGIN: 'begin' ;
END: 'end' ;
IF: 'if' ;
ELSE: 'else' ;

compilation_unit: module_declaration+ ;

module_declaration:
    'module' module_identifier '(' port_list? ')' ';'
    module_item*
    'endmodule'
    ;

module_identifier
      : Identifier
      ;

port_list: port (',' port)* ;
port:
      ('input' | 'output') data_type range? Identifier (',' Identifier)*
    ;
range: '[' expression ':' expression ']';

data_type: 'logic' ;

module_item:
      net_declaration
    | continuous_assign
    | always_comb_block
    ;

net_declaration
    : ('logic' | 'wire') range? Identifier (',' Identifier)* SEMICOLON
    ;

continuous_assign:
    'assign' variable_lvalue ASSIGN expression SEMICOLON
    ;

always_comb_block:
    'always_comb' statement ;

statement:
      '{' statement* '}'                   
    | begin_end_block
    | blocking_assignment
    | if_statement
    | case_statement
    ;

blocking_assignment
    : variable_lvalue ASSIGN expression SEMICOLON
    ;

variable_lvalue
    : Identifier ( '[' expression ']' | '[' expression ':' expression ']' )*
    ;

begin_end_block
    : BEGIN statement* END
    ;

if_statement
    : IF '(' expression ')' statement (ELSE statement)?
    ;

case_statement:
    CASE '(' expression ')' case_item+ ENDCASE
    ;

case_item
    : expression_list COLON statement
    | DEFAULT COLON statement
    ;
expression_list
    : expression (COMMA expression)*
    ;

expression
    : '!' expression                               #LogicalNotExpr
    | '~' expression                               #BitwiseNotExpr
    | '-' expression                               #NegateExpr
    | expression '&' expression                    #AndExpr
    | expression '|' expression                    #OrExpr
    | expression '^' expression                    #XorExpr
    | expression '~^' expression                   #XnorExpr
    | expression '==' expression                   #EqExpr
    | expression '[' expression ']'                #BitSelectExpr
    | expression '[' expression ':' expression ']' #PartSelectExpr
    | '{' expression (',' expression)* '}'         #ConcatExpr
    | '(' expression ')'                           #ParenExpr
    | literal                                      #ConstExpr
    | Identifier                                   #IdExpr
    ;

literal:
      DecimalNumber
    | BinaryLiteral
    | HexLiteral
    | DecLiteral
    ;


Identifier: [a-zA-Z_][a-zA-Z_0-9]* ;
DecimalNumber: [0-9]+ ;

BinaryLiteral : DecimalNumber '\'' [bB] [01xXzZ]+ ;
HexLiteral    : DecimalNumber '\'' [hH] [0-9a-fA-FxXzZ]+ ;
DecLiteral    : DecimalNumber '\'' [dD] [0-9]+ ;

WS: [ \t\r\n]+ -> skip ;
LINE_COMMENT
    : '//' ~[\r\n]* -> skip
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> skip
    ;
