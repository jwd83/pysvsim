// 1-to-4 Demultiplexer built from basic logic gates
// Routes input IN to one of OUT0–OUT3 based on select lines SEL1:SEL0
//
// Truth Table:
// SEL1 SEL0 | OUT0 OUT1 OUT2 OUT3
// ---------|---------------------
//   0    0  |  IN    0    0    0
//   0    1  |   0   IN    0    0
//   1    0  |   0    0   IN    0
//   1    1  |   0    0    0   IN

module demux_1to4 (
    input  IN,       // Data input
    input  SEL1,     // Most significant select bit
    input  SEL0,     // Least significant select bit
    output OUT0,     // Output for SEL=00
    output OUT1,     // Output for SEL=01
    output OUT2,     // Output for SEL=10
    output OUT3      // Output for SEL=11
);

    // Internal signals for inverted select lines
    logic not_sel0;
    logic not_sel1;

    // Internal AND combinations
    logic sel_00;  // ~SEL1 & ~SEL0
    logic sel_01;  // ~SEL1 &  SEL0
    logic sel_10;  //  SEL1 & ~SEL0
    logic sel_11;  //  SEL1 &  SEL0

    // Invert select bits
    inverter u_not_sel0 (.in(SEL0), .out(not_sel0));
    inverter u_not_sel1 (.in(SEL1), .out(not_sel1));

    // Generate the four selection signals using AND gates
    and_gate u_and_00 (.inA(not_sel1), .inB(not_sel0), .outY(sel_00));
    and_gate u_and_01 (.inA(not_sel1), .inB(SEL0),     .outY(sel_01));
    and_gate u_and_10 (.inA(SEL1),     .inB(not_sel0), .outY(sel_10));
    and_gate u_and_11 (.inA(SEL1),     .inB(SEL0),     .outY(sel_11));

    // Gate the input with the selection lines
    and_gate u_out0 (.inA(IN), .inB(sel_00), .outY(OUT0));
    and_gate u_out1 (.inA(IN), .inB(sel_01), .outY(OUT1));
    and_gate u_out2 (.inA(IN), .inB(sel_10), .outY(OUT2));
    and_gate u_out3 (.inA(IN), .inB(sel_11), .outY(OUT3));

endmodule
