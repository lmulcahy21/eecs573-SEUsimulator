module rca #(parameter WIDTH = 64) (
    input  [WIDTH-1:0] A, B,
    input              carry_in,
    output [WIDTH-1:0] S,
    output             carry_out
);
    logic [WIDTH-2:0] carries;

    fa adders [WIDTH-1:0] (
        .A(A), .B(B), .carry_in({carries, carry_in}),
        .S(S), .carry_out({carry_out, carries})
    );

endmodule
