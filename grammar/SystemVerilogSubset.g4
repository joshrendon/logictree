
grammar SystemVerilogSubset;

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
      'input' data_type range? Identifier
    | 'output' data_type range? Identifier
    ;
range: '[' DecimalNumber ':' DecimalNumber ']';

data_type: 'logic' ;

module_item:
      net_declaration
    | continuous_assign
    | always_comb_block
    ;

net_declaration:
    ('logic' | 'wire') Identifier ';' ;

continuous_assign:
    'assign' Identifier '=' expression ';'
    ;

always_comb_block:
    'always_comb' statement ;

statement:
      '{' statement* '}'                   // SystemVerilog block
    | begin_end_block
    | Identifier '=' expression ';'       // assignment
    | ifStatement
    | case_statement
    ;

begin_end_block
    : 'begin' statement* 'end'
    ;

ELSE: 'else' ;

ifStatement
    : 'if' '(' expression ')' statement (ELSE statement)?
    ;

case_statement:
    'case' '(' expression ')' case_item+ 'endcase'
    ;

case_item
    : literal ':' statement
    | 'default' ':' statement
    ;

expression
    : '!' expression                   #LogicalNotExpr
    | '~' expression                   #BitwiseNotExpr
    | '-' expression                   #NegateExpr
    | expression '&' expression        #AndExpr
    | expression '|' expression        #OrExpr
    | expression '^' expression        #XorExpr
    | expression '~^' expression       #XnorExpr
    | expression '==' expression       #EqExpr
    | '(' expression ')'               #ParenExpr
    | literal                          #ConstExpr
    | Identifier                       #IdExpr
    ;

literal:
      DecimalNumber
    | BinaryLiteral
    ;

BinaryLiteral: DecimalNumber '\'' [bB] [01xXzZ]+ ;
Identifier: [a-zA-Z_][a-zA-Z_0-9]* ;
DecimalNumber: [0-9]+ ;

WS: [ \t\r\n]+ -> skip ;
LINE_COMMENT
    : '//' ~[\r\n]* -> skip
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> skip
    ;
