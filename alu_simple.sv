module alu_simple (
    input A,
    input B,
    input Op0,
    output Result
);
    // Simple 2-operation ALU: 0=AND, 1=OR
    wire and_result, or_result;
    
    assign and_result = A & B;
    assign or_result = A | B;
    
    // Select operation based on Op0
    assign Result = (~Op0 & and_result) | (Op0 & or_result);
    
endmodule