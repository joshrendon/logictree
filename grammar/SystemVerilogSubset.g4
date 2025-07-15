grammar SystemVerilogSubset;

compilation_unit: module_declaration+ ;

module_declaration: 'module' Identifier '(' port_list? ')' ';'
                    module_item* 'endmodule' ;

port_list: port (',' port)* ;
port: 'input' data_type Identifier
    | 'output' data_type Identifier ;

data_type: 'logic' ;

module_item: net_declaration
           | continuous_assign
           | always_comb_block ;

net_declaration: ('logic' | 'wire') Identifier ';' ;

continuous_assign: 'assign' Identifier '=' expression ';' ;

always_comb_block: 'always_comb' statement ;

statement
    : '{' statement* '}'                   // block (SystemVerilog-style)
    | 'begin' statement* 'end'             // block (Verilog-style)
    | Identifier '=' expression ';'        // assignment
    | case_statement                        // case
    ;

case_statement
    : 'case' '(' expression ')' case_item+ default_item? 'endcase'
    ;

case_item
    : expression ':' statement
    ;

default_item
    : 'default' ':' statement
    ;

// Expressions
expression: logical_or_expression ;

logical_or_expression
    : logical_or_expression '|' logical_xor_expression    # OrExpr
    | logical_xor_expression                              # OrPass
    ;

logical_xor_expression
    : logical_xor_expression '^' logical_and_expression   # XorExpr
    | logical_and_expression                              # XorPass
    ;

logical_and_expression
    : logical_and_expression '&' unary_expression         # AndExpr
    | unary_expression                                    # AndPass
    ;

unary_expression
    : '!' unary_expression                                # NotExpr
    | '~' unary_expression                                # BitNotExpr
    | '-' unary_expression                                # NegateExpr
    | primary_expression                                  # PrimaryPass
    ;

primary_expression
    : Identifier                    # IdExpr
    | Number                        # NumExpr
    | '(' expression ')'           # ParenExpr
    ;

Identifier: [a-zA-Z_][a-zA-Z0-9_]* ;
Number: [0-9]+ ;

WS: [ \t\r\n]+ -> skip ;
