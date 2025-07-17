
grammar SystemVerilogSubset;

compilation_unit: module_declaration+ ;

module_declaration:
    'module' Identifier '(' port_list? ')' ';'
    module_item*
    'endmodule'
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
    | 'begin' statement* 'end'             // Verilog-style block
    | Identifier '=' expression ';'       // assignment
    | case_statement
    ;

case_statement:
    'case' '(' expression ')' case_item+ 'endcase'
    ;

case_item:
    literal ':' statement
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

