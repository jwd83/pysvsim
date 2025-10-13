module adder_4bit (
    input A0,
    input A1,
    input A2,
    input A3,
    input B0,
    input B1,
    input B2,
    input B3,
    input Cin,
    output S0,
    output S1,
    output S2,
    output S3,
    output Cout
);
    // 4-bit ripple carry adder built from 4 full_adder modules
    // Carry propagates from bit 0 (LSB) to bit 3 (MSB)
    
    wire C1, C2, C3;  // Internal carry signals
    
    // Bit 0 (LSB) - uses input carry Cin
    full_adder fa0 (
        .A(A0),
        .B(B0),
        .Cin(Cin),
        .Sum(S0),
        .Cout(C1)
    );
    
    // Bit 1 - uses carry from bit 0
    full_adder fa1 (
        .A(A1),
        .B(B1),
        .Cin(C1),
        .Sum(S1),
        .Cout(C2)
    );
    
    // Bit 2 - uses carry from bit 1
    full_adder fa2 (
        .A(A2),
        .B(B2),
        .Cin(C2),
        .Sum(S2),
        .Cout(C3)
    );
    
    // Bit 3 (MSB) - uses carry from bit 2, generates final carry out
    full_adder fa3 (
        .A(A3),
        .B(B3),
        .Cin(C3),
        .Sum(S3),
        .Cout(Cout)
    );
    
endmodule