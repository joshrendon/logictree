module tb_delivery;
    logic C, T, A;
    logic D;

    golden_delivery uut (
        .customs_cleared(C),
        .transit_ready(T),
        .arrived_on_truck(A),
        .delivery_confirmed(D)
    );

    initial begin
        // All 0 –> No delivery
        C = 0; T = 0; A = 0; #10;
        $display("D = %0b (expected 0)", D);

        // Customs cleared, not ready for transit
        C = 1; T = 0; A = 0; #10;
        $display("D = %0b (expected 0)", D);

        // All ready but not on truck
        C = 1; T = 1; A = 0; #10;
        $display("D = %0b (expected 0)", D);

        // Ready for glorious delivery
        C = 1; T = 1; A = 1; #10;
        $display("D = %0b (expected 1)", D);

        $finish;
    end
endmodule
