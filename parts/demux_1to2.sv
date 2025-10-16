// 1-to-2 Demultiplexer built from basic logic gate modules
// Routes input IN to either OUT0 or OUT1 depending on select SEL.
//
// Truth Table:
// SEL | OUT0 | OUT1
// ----|-------|------
//  0  |  IN   |  0
//  1  |   0   |  IN

module demux_1to2 (
    input  IN,     // Input data
    input  SEL,    // Select line
    output OUT0,   // Output when SEL = 0
    output OUT1    // Output when SEL = 1
);

    // Internal wires
    logic not_sel;       // Inverted select
    logic in_and_not_sel;
    logic in_and_sel;

    // Invert select: not_sel = ~SEL
    inverter u_not_sel (
        .in(SEL),
        .out(not_sel)
    );

    // OUT0 = IN AND (NOT SEL)
    and_gate u_and0 (
        .inA(IN),
        .inB(not_sel),
        .outY(in_and_not_sel)
    );

    // OUT1 = IN AND SEL
    and_gate u_and1 (
        .inA(IN),
        .inB(SEL),
        .outY(in_and_sel)
    );

    // Drive final outputs
    assign OUT0 = in_and_not_sel;
    assign OUT1 = in_and_sel;

endmodule
