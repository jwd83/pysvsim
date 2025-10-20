// ===========================================================
// 8-Bit Carry Select Adder
// ===========================================================
// Inputs: inA[7:0], inB[7:0], inCarry
// Outputs: outSum[7:0], outCarry
//
// This carry select adder improves performance by computing both
// possible outcomes for the upper 4 bits in parallel:
// 1. Lower 4 bits computed normally: inA[3:0] + inB[3:0] + inCarry
// 2. Upper 4 bits computed with carry=0: inA[7:4] + inB[7:4] + 0
// 3. Upper 4 bits computed with carry=1: inA[7:4] + inB[7:4] + 1
// 4. Use actual carry from lower 4 bits to select correct upper result
//
// Performance: Critical path is lower 4-bit adder + multiplexer delay
// Cost: Requires 3 adders + multiplexers instead of 2 adders
//
// NAND Gate Analysis:
// - Lower 4-bit adder: 60 NANDs
// - Upper 4-bit adder (carry=0): 60 NANDs
// - Upper 4-bit adder (carry=1): 60 NANDs
// - 4-bit result multiplexer: 4 × 8 = 32 NANDs (4 × (1+2+3) per 1-bit mux)
// - 1-bit carry multiplexer: 8 NANDs
// Total: ~220 NANDs vs 120 NANDs for ripple carry (83% overhead)

module adder_cs_8bit (
    input  logic [7:0] inA,      // 8-bit input A
    input  logic [7:0] inB,      // 8-bit input B
    input  logic       Cin,      // Initial carry-in
    output logic [7:0] outSum,   // 8-bit sum output
    output logic       Cout      // Final carry-out
);
    // Signals for lower 4-bit adder (always computed)
    logic [3:0] sum_lower;
    logic       carry_from_lower;

    // Signals for upper 4-bit adder with carry=0
    logic [3:0] sum_upper_c0;
    logic       carry_upper_c0;

    // Signals for upper 4-bit adder with carry=1
    logic [3:0] sum_upper_c1;
    logic       carry_upper_c1;

    // Lower 4-bit adder (bits 3:0) - always computed
    adder_4bit u_lower (
        .inA(inA[3:0]),
        .inB(inB[3:0]),
        .inCarry(Cin),
        .outSum(sum_lower),
        .outCarry(carry_from_lower)
    );

    // Upper 4-bit adder assuming carry=0
    adder_4bit u_upper_c0 (
        .inA(inA[7:4]),
        .inB(inB[7:4]),
        .inCarry(1'b0),            // Assume no carry
        .outSum(sum_upper_c0),
        .outCarry(carry_upper_c0)
    );

    // Upper 4-bit adder assuming carry=1
    adder_4bit u_upper_c1 (
        .inA(inA[7:4]),
        .inB(inB[7:4]),
        .inCarry(1'b1),            // Assume carry
        .outSum(sum_upper_c1),
        .outCarry(carry_upper_c1)
    );

    // Multiplexers to select correct upper result based on actual carry
    mux_2to1_4bit u_sum_mux (
        .in0(sum_upper_c0),        // Select when carry_from_lower = 0
        .in1(sum_upper_c1),        // Select when carry_from_lower = 1
        .sel(carry_from_lower),
        .out(outSum[7:4])
    );

    mux_2to1_1bit u_carry_mux (
        .in0(carry_upper_c0),      // Select when carry_from_lower = 0
        .in1(carry_upper_c1),      // Select when carry_from_lower = 1
        .sel(carry_from_lower),
        .out(Cout)
    );

    // Lower sum bits connect directly (no selection needed)
    assign outSum[3:0] = sum_lower;

endmodule