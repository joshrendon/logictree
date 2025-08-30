module m(input logic s0,s1, d0,d1,d2, output logic y);
  always_comb begin
    if (s0) y = d0;
    else if (s1) y = d1;
    else y = d2;
  end
endmodule
