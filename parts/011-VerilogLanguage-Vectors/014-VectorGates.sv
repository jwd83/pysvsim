module top_module(
    input [2:0] a,
    input [2:0] b,
    output [2:0] out_or_bitwise,
    output out_or_logical,
    output [5:0] out_not
);

    assign out_not[5:3] = ~b[2:0];
    assign out_not[2:0] = ~a[2:0];

    assign out_or_bitwise = a | b;

    // original solution
    // assign out_or_logical = a[0] | a[1] | a[2] | b[0] | b[1] | b[2];

    // alternative solution with reduction operators
    assign out_or_logical = |a | |b;

endmodule
