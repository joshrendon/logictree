module expr_simp (
    input  logic        valid,
    input  logic [6:0]  opcode,
    input  logic        funct7b5,
    output logic        is_add
);

    assign is_add   = valid & (opcode == 7'b0110011) &  ~funct7b5;
endmodule
