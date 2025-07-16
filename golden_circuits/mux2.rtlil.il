attribute \cells_not_processed 1
attribute \src "golden_circuits/mux2.sv:1.1-16.10"
module \mux2
  attribute \src "golden_circuits/mux2.sv:0.0-0.0"
  wire $1\out[0:0]
  attribute \src "golden_circuits/mux2.sv:0.0-0.0"
  wire $0\out[0:0]
  attribute \src "golden_circuits/mux2.sv:5.16-5.19"
  wire output 4 \out
  attribute \src "golden_circuits/mux2.sv:4.15-4.16"
  wire input 3 \s
  attribute \src "golden_circuits/mux2.sv:3.15-3.16"
  wire input 2 \b
  attribute \src "golden_circuits/mux2.sv:2.15-2.16"
  wire input 1 \a
  attribute \always_comb 1
  attribute \src "golden_circuits/mux2.sv:0.0-0.0"
  process $proc$golden_circuits/mux2.sv:0$1
    assign { } { }
    assign $0\out[0:0] $1\out[0:0]
    attribute \src "golden_circuits/mux2.sv:9.5-13.12"
    switch { 31'0000000000000000000000000000000 \s }
      attribute \src "golden_circuits/mux2.sv:0.0-0.0"
      case 0
        assign { } { }
        assign $1\out[0:0] \a
      attribute \src "golden_circuits/mux2.sv:0.0-0.0"
      case 1
        assign { } { }
        assign $1\out[0:0] \b
      attribute \src "golden_circuits/mux2.sv:0.0-0.0"
      case 
        assign { } { }
        assign $1\out[0:0] 1'0
    end
    sync always
      update \out $0\out[0:0]
  end
end
