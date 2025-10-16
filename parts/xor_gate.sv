module xor_gate (
    input inA,
    input inB,
    output outY
);
    // XOR gate built using: A ⊕ B = (A & ~B) | (~A & B)
    // Step 1: Invert A and B
    wire not_A, not_B;
    inverter inv1 (
        .in(inA),
        .out(not_A)
    );
    
    inverter inv2 (
        .in(inB),
        .out(not_B)
    );
    
    // Step 2: Generate A & ~B
    wire a_and_not_b;
    and_gate and1 (
        .inA(inA),
        .inB(not_B),
        .outY(a_and_not_b)
    );
    
    // Step 3: Generate ~A & B
    wire not_a_and_b;
    and_gate and2 (
        .inA(not_A),
        .inB(inB),
        .outY(not_a_and_b)
    );
    
    // Step 4: OR the results: (A & ~B) | (~A & B)
    or_gate or1 (
        .inA(a_and_not_b),
        .inB(not_a_and_b),
        .outY(outY)
    );
endmodule