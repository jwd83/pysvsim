module half_adder (
    input A,
    input B,
    output Sum,
    output Carry
);
    // Half adder built using hierarchical modules:
    // Sum = A XOR B (using xor_gate module)
    // Carry = A AND B (using and_gate module)
    
    xor_gate xor1 (
        .inA(A),
        .inB(B),
        .outY(Sum)
    );
    
    and_gate and1 (
        .inA(A),
        .inB(B),
        .outY(Carry)
    );
endmodule
