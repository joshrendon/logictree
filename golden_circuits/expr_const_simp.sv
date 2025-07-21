module expr_simp (
    input  logic        valid,
    input  logic [3:0]  opcode,
    output logic        is_add
);

    assign is_add   = valid & (opcode == 4'b0011);
endmodule
