// Mux2 module
module mux2 (
  input logic a,
  input logic b,
  input logic s,
  output logic out
);

  always_comb begin
    case (s)
      0: out = a;
      1: out = b;
    endcase
  end

endmodule

