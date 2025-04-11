// Testbench for Kogge-Stone Adder
module adder_tb;
    parameter WIDTH = 64;
    logic [WIDTH-1:0] a, b;
    logic [WIDTH-1:0] sum;
    logic cout;

    ksa #(WIDTH) dut (
        .operand_a_i(a),
        .operand_b_i(b),
        .result_o(sum),
        .overflow_o(cout)
    );

    initial begin
        // Test cases
        a = 32'h00000001;
        b = 32'h00000001;
        #10;
        $display("A = %h, B = %h, SUM = %h, COUT = %b", a, b, sum, cout);

        a = 32'hFFFFFFFF;
        b = 32'h00000001;
        #10;
        $display("A = %h, B = %h, SUM = %h, COUT = %b", a, b, sum, cout);

        a = 32'hAAAA5555;
        b = 32'h5555AAAA;
        #10;
        $display("A = %h, B = %h, SUM = %h, COUT = %b", a, b, sum, cout);

        a = 32'h12345678;
        b = 32'h87654321;
        #10;
        $display("A = %h, B = %h, SUM = %h, COUT = %b", a, b, sum, cout);

        $finish;
    end
endmodule
