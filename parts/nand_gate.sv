module nand_gate (
    input inA,
    input inB,
    output outY
);
    assign outY = ~(inA & inB);
endmodule