module if_tree_simple(
    input logic sel,
    input logic a,
    input logic b,
    output logic out
);

always_comb begin
    if (sel == 1'b1)
        out = a;
    else begin
        out = b;
    end
end

endmodule
