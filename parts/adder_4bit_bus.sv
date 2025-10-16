// 4-bit Ripple-Carry Adder using Bus Notation
// Demonstrates proper SystemVerilog bus syntax
module adder_4bit_bus (
    input [3:0] A,      // 4-bit input bus A
    input [3:0] B,      // 4-bit input bus B  
    input Cin,          // Carry input
    output [3:0] Sum,   // 4-bit sum output bus
    output Cout         // Carry output
);

    // Internal carry wires
    wire C1, C2, C3;
    
    // Instantiate full adders for each bit
    // Bit 0 (LSB)
    full_adder fa0 (
        .A(A[0]),
        .B(B[0]),
        .Cin(Cin),
        .Sum(Sum[0]),
        .Cout(C1)
    );
    
    // Bit 1
    full_adder fa1 (
        .A(A[1]),
        .B(B[1]),
        .Cin(C1),
        .Sum(Sum[1]),
        .Cout(C2)
    );
    
    // Bit 2
    full_adder fa2 (
        .A(A[2]),
        .B(B[2]),
        .Cin(C2),
        .Sum(Sum[2]),
        .Cout(C3)
    );
    
    // Bit 3 (MSB)
    full_adder fa3 (
        .A(A[3]),
        .B(B[3]),
        .Cin(C3),
        .Sum(Sum[3]),
        .Cout(Cout)
    );

endmodule