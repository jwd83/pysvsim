// 4:1 Multiplexer using bus notation
// Built hierarchically using basic logic gates
module mux_4to1 (
    input A,B,C,D,          // 4 single-bit data inputs (A, B, C, D)
    input [1:0] select,     // 2-bit select input bus (00=A, 01=B, 10=C, 11=D)
    output out              // Single-bit output
);

    // Internal wires for decoded select signals
    wire sel_00, sel_01, sel_10, sel_11;  // Decoded select combinations
    wire not_s0, not_s1;                  // Inverted select signals
    wire and0_out, and1_out, and2_out, and3_out;  // AND gate outputs

    // Create inverted select signals using inverter modules
    inverter inv_s0 (
        .in(select[0]),
        .out(not_s0)
    );

    inverter inv_s1 (
        .in(select[1]),
        .out(not_s1)
    );

    // Decode select signals using AND gates
    // sel_00 = ~S1 & ~S0 (select input 0)
    and_gate decode_00 (
        .inA(not_s1),
        .inB(not_s0),
        .outY(sel_00)
    );

    // sel_01 = ~S1 & S0 (select input 1)
    and_gate decode_01 (
        .inA(not_s1),
        .inB(select[0]),
        .outY(sel_01)
    );

    // sel_10 = S1 & ~S0 (select input 2)
    and_gate decode_10 (
        .inA(select[1]),
        .inB(not_s0),
        .outY(sel_10)
    );

    // sel_11 = S1 & S0 (select input 3)
    and_gate decode_11 (
        .inA(select[1]),
        .inB(select[0]),
        .outY(sel_11)
    );

    // Gate each data input with its corresponding select signal
    and_gate gate_data0 (
        .inA(A),
        .inB(sel_00),
        .outY(and0_out)
    );

    and_gate gate_data1 (
        .inA(B),
        .inB(sel_01),
        .outY(and1_out)
    );

    and_gate gate_data2 (
        .inA(C),
        .inB(sel_10),
        .outY(and2_out)
    );

    and_gate gate_data3 (
        .inA(D),
        .inB(sel_11),
        .outY(and3_out)
    );

    // Combine all gated outputs using OR gates in a tree structure
    wire or_01, or_23;  // Intermediate OR results

    or_gate combine_01 (
        .inA(and0_out),
        .inB(and1_out),
        .outY(or_01)
    );

    or_gate combine_23 (
        .inA(and2_out),
        .inB(and3_out),
        .outY(or_23)
    );

    // Final OR to combine all paths
    or_gate final_or (
        .inA(or_01),
        .inB(or_23),
        .outY(out)
    );

endmodule