module half_adder (
    input A,
    input B,
    output Sum,
    output Carry
);
    // Half adder logic:
    // Sum = A XOR B
    // Carry = A AND B
    assign Sum = A ^ B;
    assign Carry = A & B;
endmodule