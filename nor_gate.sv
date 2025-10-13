module nor_gate (
    input inA,
    input inB,
    output outY
);
    // NOR gate built using NOT OR: ~(A | B)
    // Step 1: Generate OR of inputs
    wire or_result;
    or_gate or1 (
        .inA(inA),
        .inB(inB),
        .outY(or_result)
    );
    
    // Step 2: Invert the OR result to get NOR
    inverter inv1 (
        .in(or_result),
        .out(outY)
    );
endmodule