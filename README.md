
## Logictree: SystemVerilog Static Logic Analyzer — Project Status Summary

This project is an open-source Python-based symbolic analysis toolchain for SystemVerilog logic expressions and RTL constructs.
It parses a subset of SystemVerilog using ANTLR4 and converts it into an internal symbolic intermediate representation (IR) called LogicTree.
The LogicTree IR enables structural analysis, visualization, and back end transformations.

### Supported Features:
#### Core Parser (ANTLR4-based)
- [x] SystemVerilog subset grammar implemented in SystemVerilogSubset.g4
- [x] Supports module, input, output, assign statements
- [x] Supports if and case statements (basic form)
- [x] Supports binary expressions: &, |, ^, ~, ==, !=, bitvector literals (e.g., 3'b101)
- [x] Partial support for ~, parentheses, and unary operations
#### AST + IR Pipeline
- [x] Full AST generation via ANTLR4 parse tree to custom Python AST classes
- [x] LogicTree IR representation for symbolic Boolean structure
- [x] Node types: And, Or, Not, Xor, Eq, Id, Const
- [x] Bitvector equality comparisons expanded to logic trees (e.g., funct3 == 3'b000)
- [x] Depth-aware analysis (tracks maximum path depth from inputs)
#### Visualization
- [x] to_dot() and Graphviz .png/.svg rendering of logic trees
- [x]  Balanced reduction option for n-input AND/OR gates (--balanced)
- [x] Tagging support for constant-time reductions
#### CLI Tooling
- [x] CLI frontend (cli.main) supports:
- [x] File parsing
- [x] LogicTree analysis
- [x] DOT and image export (--to_dot, --to_png, --to_svg)
- [x] Debug logging (--debug-log)
- [x] Flattening/balancing options
#### Extensible Infrastructure
   Visitors and Lowering Passes:
   - AST visitor extracts assign expressions to LogicTree
   - Partial case → if lowering in progress
   - IR collector for introspection, future Verilog or JSON export

In Progress / Planned Enhancements

|Feature|Status|Notes|
|-------|---------|------|
|case → if lowering  |🔄 In progress|Partial lowering implemented; full transformation planned|
|if → mux lowering|🔜 Planned|Will enable hardware-oriented synthesis and depth estimation|
|to_verilog() output|🔜 Planned|Will regenerate simplified RTL from LogicTree IR|
|to_bdd() backend|🧪 Scaffolded|Initial plan written; to support BDD introspection|
|Signal name → LogicTree mapping|✅ Done|Enables per-signal symbolic inspection|
|AST ↔ LogicTree cross-reference|✅ Attached IR|AST nodes decorated with .logic_tree attribute|
|assign logic depth estimation|✅ Supported|Includes coarse vs. fine depth estimation|
|CLI: --strip-tags, --flatten| 🔜 Planned |Simplifies output for easier downstream use|
|Comments in grammar|🔜 Planned|To allow ignoring or preserving comments in AST|

---
Philosophy and Use Case

This tool is designed for symbolic logic analysis, enabling:
* Pre-synthesis decoder optimization
* RTL logic depth estimation
* Visualization of complex Boolean expressions
* Research and educational insight into logic structure

It’s especially suited to analyzing RISC-V instruction decoders, and will serve as the foundation 
for future articles, tutorials, and FPGA validation studies.

Generating new visitor modules from grammar:
cd grammar/
antlr -Dlanguage=Python3 <grammar.g4>
antlr -Dlanguage=Python3 -visitor <grammar.g4>  # To generate a visitor file
