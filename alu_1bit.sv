module alu_1bit (
    input A,        // First operand
    input B,        // Second operand
    input Cin,      // Carry in (for ADD operation)
    input Op0,      // Operation select bit 0
    input Op1,      // Operation select bit 1
    output Result,  // ALU result
    output Cout     // Carry out (for ADD operation)
);
    // Hierarchical 1-bit ALU with 4 operations:
    // 00: AND
    // 01: OR
    // 10: XOR
    // 11: ADD (using full adder)
    
    // Generate all possible results using our gate modules
    wire and_result, or_result, xor_result;
    wire add_result, add_cout;
    
    // Logic operations using our gate modules
    and_gate and_op (
        .inA(A),
        .inB(B),
        .outY(and_result)
    );
    
    or_gate or_op (
        .inA(A),
        .inB(B),
        .outY(or_result)
    );
    
    xor_gate xor_op (
        .inA(A),
        .inB(B),
        .outY(xor_result)
    );
    
    // Arithmetic operation using full adder module
    full_adder add_op (
        .A(A),
        .B(B),
        .Cin(Cin),
        .Sum(add_result),
        .Cout(add_cout)
    );
    
    // Operation select logic - build a 2-to-4 decoder using gates
    wire sel_and, sel_or, sel_xor, sel_add;
    
    // Generate selection signals: ~Op1 & ~Op0 = 00 (AND)
    wire not_op0, not_op1;
    inverter inv0 (.in(Op0), .out(not_op0));
    inverter inv1 (.in(Op1), .out(not_op1));
    
    and_gate sel_and_gate (.inA(not_op1), .inB(not_op0), .outY(sel_and)); // 00
    and_gate sel_or_gate (.inA(not_op1), .inB(Op0), .outY(sel_or));       // 01
    and_gate sel_xor_gate (.inA(Op1), .inB(not_op0), .outY(sel_xor));     // 10
    and_gate sel_add_gate (.inA(Op1), .inB(Op0), .outY(sel_add));         // 11
    
    // Result multiplexer using AND-OR logic with our gate modules
    wire result_and, result_or, result_xor, result_add;
    
    and_gate mux_and (.inA(sel_and), .inB(and_result), .outY(result_and));
    and_gate mux_or (.inA(sel_or), .inB(or_result), .outY(result_or));
    and_gate mux_xor (.inA(sel_xor), .inB(xor_result), .outY(result_xor));
    and_gate mux_add (.inA(sel_add), .inB(add_result), .outY(result_add));
    
    // OR all the multiplexed results together
    wire temp_result1, temp_result2;
    or_gate or_result1 (.inA(result_and), .inB(result_or), .outY(temp_result1));
    or_gate or_result2 (.inA(result_xor), .inB(result_add), .outY(temp_result2));
    or_gate final_result (.inA(temp_result1), .inB(temp_result2), .outY(Result));
    
    // Carry out multiplexer - only ADD operation produces carry
    and_gate carry_mux (.inA(sel_add), .inB(add_cout), .outY(Cout));
    
endmodule