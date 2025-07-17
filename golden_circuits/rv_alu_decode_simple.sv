module rv_alu_decode (
    input  logic        valid,
    input  logic [6:0]  opcode,
    input  logic [2:0]  funct3,
    input  logic        funct7b5,
    output logic        is_add,
    output logic        is_sub,
    output logic        is_and,
    output logic        is_or
);

    assign is_add   = valid & (opcode == 7'b0110011) & (funct3 == 3'b000) & ~funct7b5;
    assign is_sub   = valid & (opcode == 7'b0110011) & (funct3 == 3'b000) &  funct7b5;
    assign is_and   = valid & (opcode == 7'b0110011) & (funct3 == 3'b111);
    assign is_or    = valid & (opcode == 7'b0110011) & (funct3 == 3'b110);
endmodule
