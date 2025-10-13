module inverter (
    input in,
    output out
);
    // Create an inverter using a NAND gate
    // By tying both NAND inputs together, we get: out = ~(in & in) = ~in
    nand_gate u1 (
        .inA(in),
        .inB(in),
        .outY(out)
    );
endmodule