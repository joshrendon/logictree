// MIT License
//

module rv_alu_decode (
    input logic [6:0] opcode,
    input logic [2:0] funct3,
    input logic [6:0] funct7,
    output logic [3:0] alu_op // One-hot-type encoding for opcode
);
    always_comb begin
        unique casez ( {funct7, funct3, opcode})
            //ADD (funct7 = 0, funct3 = 000)
            17'b0000000_000_0110011: alu_op = 4'd0;
            //SUB (funct7 = 0100000, funct3 = 000)
            17'b0100000_000_0110011: alu_op = 4'd1;
            //AND
            17'b0000000_111_0110011 : alu_op = 4'd2;
            //OR
            17'b0000000_110_0110011 : alu_op = 4'd3;
            default : alu_op = 4'hF; // Illegal opcode

        endcase
    end
endmodule : rv_alu_decode
