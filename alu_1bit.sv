module alu_1bit (
    input A,        // First operand
    input B,        // Second operand
    input Cin,      // Carry/borrow in
    input Op0,      // Operation select bit 0
    input Op1,      // Operation select bit 1
    input Op2,      // Operation select bit 2
    output Result,  // ALU result
    output Cout     // Carry/borrow out
);
    // Result using completely inline expressions based on operation select
    assign Result = 
        // 000: AND
        ((~Op2 & ~Op1 & ~Op0) & (A & B)) |
        // 001: OR  
        ((~Op2 & ~Op1 &  Op0) & (A | B)) |
        // 010: XOR
        ((~Op2 &  Op1 & ~Op0) & (A ^ B)) |
        // 011: ADD
        ((~Op2 &  Op1 &  Op0) & (A ^ B ^ Cin)) |
        // 100: SUB 
        (( Op2 & ~Op1 & ~Op0) & (A ^ (~B) ^ Cin)) |
        // 101: NOT A
        (( Op2 & ~Op1 &  Op0) & (~A)) |
        // 110: Pass A
        (( Op2 &  Op1 & ~Op0) & A) |
        // 111: Pass B
        (( Op2 &  Op1 &  Op0) & B);
    
    // Carry out for ADD and SUB operations only
    assign Cout = 
        // ADD carry out
        ((~Op2 &  Op1 &  Op0) & ((A & B) | (A & Cin) | (B & Cin))) |
        // SUB carry out  
        (( Op2 & ~Op1 & ~Op0) & ((A & (~B)) | (A & Cin) | ((~B) & Cin)));
    
endmodule
