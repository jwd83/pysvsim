module or_gate (
    input inA,
    input inB,
    output outY
);
    // OR gate built using De Morgan's law: A | B = ~(~A & ~B)
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
    
    // Step 2: NAND the inverted inputs: ~A NAND ~B = ~(~A & ~B) = A | B
    nand_gate nand1 (
        .inA(not_A),
        .inB(not_B),
        .outY(outY)
    );
endmodule