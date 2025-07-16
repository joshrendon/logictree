# SystemVerilog AST


ANTLR4 + Python3 parser for a SystemVerilog subset.

Feed in a SV module into the flow and it will be converted
into a traversable AST. This can then be converted into
another IR called TreeLogic which can be simplified 
and output into the desired format: .dot/.png/.svg/.sv

---
Currently supported SV constructs:
   * Assignment
   * module
   * block
   * Case statement

