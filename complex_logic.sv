module complex_logic (
    input a,
    input b,
    input c,
    output out1,
    output out2,
    output out3
);
    // Test different operations
    assign out1 = a & b;        // AND
    assign out2 = a | c;        // OR
    assign out3 = a ^ (b & c);  // XOR with parentheses
endmodule