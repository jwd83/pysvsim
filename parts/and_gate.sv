module and_gate (
    input inA,
    input inB,
    output outY
);
    // Build AND gate from NAND + inverter
    // First get NAND result
    wire nand_out;
    nand_gate u1 (
        .inA(inA),
        .inB(inB),
        .outY(nand_out)
    );
    
    // Then invert the NAND result to get AND
    inverter u2 (
        .in(nand_out),
        .out(outY)
    );
endmodule