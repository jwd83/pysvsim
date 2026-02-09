module overture_cpu (
    input        clk,
    input        reset,
    input        run,
    input  [7:0] in_port,
    output [7:0] pc,
    output [7:0] out_port,
    output [7:0] instr_debug,
    output [7:0] r0_out,
    output [7:0] r1_out,
    output [7:0] r2_out,
    output [7:0] r3_out,
    output [7:0] r4_out,
    output [7:0] r5_out
);

    // Program ROM: loaded from JSON memory_files binding in tests.
    reg [7:0] rom [255:0];

    // Architectural registers.
    reg [7:0] r0;
    reg [7:0] r1;
    reg [7:0] r2;
    reg [7:0] r3;
    reg [7:0] r4;
    reg [7:0] r5;

    // Debug/execute temporaries.
    reg [7:0] instr;
    reg [7:0] src_value;
    reg       jump_taken;

    always_ff @(posedge clk)
        if (reset) begin
            pc        <= 8'b0;
            out_port  <= 8'b0;
            r0        <= 8'b0;
            r1        <= 8'b0;
            r2        <= 8'b0;
            r3        <= 8'b0;
            r4        <= 8'b0;
            r5        <= 8'b0;
            instr     <= 8'b0;
            src_value <= 8'b0;
            jump_taken <= 1'b0;
        end else begin
            // Avoid parser false positives by making first statement non-keyword.
            instr = instr;

            if (run) begin
                // Fetch current instruction.
                instr = rom[pc];

                // Default next PC is sequential.
                pc <= pc + 1'b1;

                // Defaults for per-instruction temporaries.
                src_value = 8'b0;
                jump_taken = 1'b0;

                case (instr[7:6])
                    // Immediate: R0 <- imm6
                    2'b00: begin
                        r0 <= instr[5:0];
                    end

                    // Calculate: R3 <- ALU(R1, R2)
                    2'b01:
                        case (instr[2:0])
                            3'b000: r3 <= r1 | r2;          // OR
                            3'b001: r3 <= ~(r1 & r2);       // NAND
                            3'b010: r3 <= ~(r1 | r2);       // NOR
                            3'b011: r3 <= r1 & r2;          // AND
                            3'b100: r3 <= r1 + r2;          // ADD
                            3'b101: r3 <= r1 - r2;          // SUB
                            default: r3 <= r3;              // Reserved opcodes
                        endcase

                    // Copy: dst <- src
                    2'b10: begin
                        // Keep this as the first statement so parser doesn't misread "begin case".
                        src_value = src_value;

                        case (instr[5:3])
                            3'b000: src_value = r0;
                            3'b001: src_value = r1;
                            3'b010: src_value = r2;
                            3'b011: src_value = r3;
                            3'b100: src_value = r4;
                            3'b101: src_value = r5;
                            3'b110: src_value = in_port;    // IN register
                            default: src_value = 8'b0;      // Source 111 reads zero
                        endcase

                        case (instr[2:0])
                            3'b000: r0 <= src_value;
                            3'b001: r1 <= src_value;
                            3'b010: r2 <= src_value;
                            3'b011: r3 <= src_value;
                            3'b100: r4 <= src_value;
                            3'b101: r5 <= src_value;
                            3'b110: out_port <= src_value;  // OUT register
                            default: out_port <= out_port;  // Destination 111 ignored
                        endcase
                    end

                    // Condition: if cond(R3) then PC <- R0
                    default: begin
                        // Keep this as the first statement so parser doesn't misread "begin case".
                        jump_taken = jump_taken;

                        case (instr[2:0])
                            3'b000: jump_taken = 1'b0;                                 // never
                            3'b001: if (r3 == 8'b0) jump_taken = 1'b1;                 // eq
                            3'b010: if (r3[7] == 1'b1) jump_taken = 1'b1;              // less
                            3'b011: if ((r3[7] == 1'b1) || (r3 == 8'b0)) jump_taken = 1'b1; // less_eq
                            3'b100: jump_taken = 1'b1;                                 // always
                            3'b101: if (r3 != 8'b0) jump_taken = 1'b1;                 // not_eq
                            3'b110: if (r3[7] == 1'b0) jump_taken = 1'b1;              // greater_eq
                            default: if ((r3[7] == 1'b0) && (r3 != 8'b0)) jump_taken = 1'b1; // greater
                        endcase

                        if (jump_taken) begin
                            pc <= r0;
                        end
                    end
                endcase
            end
        end

    assign instr_debug = instr;
    assign r0_out = r0;
    assign r1_out = r1;
    assign r2_out = r2;
    assign r3_out = r3;
    assign r4_out = r4;
    assign r5_out = r5;

endmodule
