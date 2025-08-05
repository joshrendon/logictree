module golden_delivery (
    input  logic customs_cleared,
    input  logic transit_ready,
    input  logic arrived_on_truck,
    output logic delivery_confirmed
);
    // Internal signal: shipment released after customs & transit checks
    logic shipment_released;

    assign shipment_released   = customs_cleared & transit_ready;
    assign delivery_confirmed  = shipment_released & arrived_on_truck;

endmodule

