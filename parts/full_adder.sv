module full_adder (
    input A,
    input B,
    input Cin,
    output Sum,
    output Cout
);
    // Full adder built from two half adders and an OR gate
    // First half adder: A + B
    wire sum1, carry1;
    half_adder ha1 (
        .A(A),
        .B(B),
        .Sum(sum1),
        .Carry(carry1)
    );
    
    // Second half adder: sum1 + Cin
    wire carry2;
    half_adder ha2 (
        .A(sum1),
        .B(Cin),
        .Sum(Sum),
        .Carry(carry2)
    );
    
    // Output carry is OR of both half adder carries
    assign Cout = carry1 | carry2;
endmodule