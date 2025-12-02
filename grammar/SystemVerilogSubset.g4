
grammar SystemVerilogSubset;

COLON: ':' ;
COMMA: ',' ;
SEMICOLON: ';' ;
NBASSIGN: '<=' ;
ASSIGN: '=' ;
DEFAULT: 'default' ;
CASE: 'case' ;
ENDCASE: 'endcase' ;
BEGIN: 'begin' ;
END: 'end' ;
IF: 'if' ;
ELSE: 'else' ;
UNIQUE: 'unique' ;
PRIORITY: 'priority' ;

compilation_unit
    : module_declaration+
    ;

module_declaration
    : 'module' module_identifier '(' port_list? ')' ';'
    module_item*
    'endmodule'
    ;

module_identifier
    : Identifier
    ;

port_list
    : port (',' port)*
    ;
port
    : ('input' | 'output') (data_type)? (range)? Identifier (',' Identifier)*
    ;

module_item
    : net_declaration
    | continuous_assign
    | always_construct
    ;

net_declaration
    : (data_type)? Identifier (',' Identifier)* SEMICOLON
    ;

range
    : '[' expression ':' expression ']'
    ;

data_type
    : 'logic' (range)?
    | 'wire'  (range)?
    | 'reg'   (range)?
    ;

continuous_assign
    : 'assign' variable_lvalue ASSIGN expression SEMICOLON
    ;

always_construct
    : 'always' event_control statement
    | 'always_comb' statement
    ;

event_control
    : '@' '*'         # wildcardSensitivityBare
    | '@' '(' '*' ')' # wildcardSensitivityParen
    | '@' '(' event_expression ')' # explicitSensitivity
    ;

event_expression
    : edge_identifier? expression ( 'or' edge_identifier? expression )*
    ;

edge_identifier
    : 'posedge'
    | 'negedge'
    ;

statement
    : blocking_assignment
    | nonblocking_assignment
    | case_statement
    | if_statement
    | begin_end_block
    ;

blocking_assignment
    : variable_lvalue ASSIGN expression SEMICOLON
    ;

nonblocking_assignment
    : variable_lvalue NBASSIGN expression SEMICOLON
    ;

variable_lvalue
    : Identifier ( '[' expression ']' | '[' expression ':' expression ']' )*
    ;

begin_end_block
    : 'begin' (':' Identifier)? statement* 'end'
    ;

if_statement
    : IF '(' expression ')' statement (ELSE statement)?
    ;

case_statement
    : (UNIQUE)? CASE '(' expression ')' case_item+ ENDCASE
    ;

case_item
    : expression (COLON expression)* COLON statement
    | DEFAULT COLON statement
    ;
//expression_list
//    : expression (COMMA expression)*
//    ;

expression
    : '!' expression                               #LogicalNotExpr
    | '~' expression                               #BitwiseNotExpr
    | '-' expression                               #NegateExpr
    | expression '&' expression                    #AndExpr
    | expression '|' expression                    #OrExpr
    | expression '^' expression                    #XorExpr
    | expression '~^' expression                   #XnorExpr
    | expression '==' expression                   #EqExpr
    | expression '!=' expression                   #NeqExpr
    | expression '[' expression ']'                #BitSelectExpr
    | expression '[' expression ':' expression ']' #PartSelectExpr
    | '{' expression (',' expression)* '}'         #ConcatExpr
    | '(' expression ')'                           #ParenExpr
    | literal                                      #ConstExpr
    | Identifier                                   #IdExpr
    ;

literal
    : DecimalNumber
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
