# SystemVerilog Simulator

A pure Python SystemVerilog simulator designed for game development. Players can write small hardware modules in SystemVerilog, and the simulator generates truth tables and validates designs against test cases.

## Features

- **Pure Python**: No external dependencies except standard libraries
- **Combinational Logic Support**: Handles basic logic operations (`&`, `|`, `^`, `~`)
- **Truth Table Generation**: Automatically generates truth tables for up to 256 input combinations
- **JSON Testing**: Validate designs with custom test cases
- **Game-Ready**: Designed to be easily embedded in larger Python games

## Usage

### Basic Truth Table Generation

```bash
python pysvsim.py --file nand_gate.sv
```

### With Custom Test Cases

```bash
python pysvsim.py --file nand_gate.sv --test tests_nand_gate.json
```

### Limit Input Combinations

```bash
python pysvsim.py --file alu_1bit.sv --max-combinations 32
```

## Command Line Arguments

- `--file <verilog_file>`: SystemVerilog file to simulate (required)
- `--test <json_file>`: JSON test file (optional)
- `--max-combinations N`: Maximum number of input combinations to test (default: 256)

## SystemVerilog Support

### Currently Supported

- Module declarations with input/output ports
- Basic assign statements
- Module instantiation with port connections
- Wire declarations
- Bitwise operators: `&` (AND), `|` (OR), `^` (XOR), `~` (NOT)
- Parentheses for expression grouping
- Single-bit scalar signals

### Example SystemVerilog Module

```verilog
module nand_gate (
    input inA,
    input inB,
    output outY
);
    assign outY = ~(inA & inB);
endmodule
```

### Module Instantiation Example

```verilog
module inverter (
    input in,
    output out
);
    // Create an inverter using a NAND gate
    nand_gate u1 (
        .inA(in),
        .inB(in),
        .outY(out)
    );
endmodule
```

## Test File Format

Test cases are specified in JSON format:

```json
[
  {"inA": 0, "inB": 0, "expect": {"outY": 1}},
  {"inA": 0, "inB": 1, "expect": {"outY": 1}},
  {"inA": 1, "inB": 0, "expect": {"outY": 1}},
  {"inA": 1, "inB": 1, "expect": {"outY": 0}}
]
```

Each test case contains:
- Input signal values (all inputs must be specified)
- `expect` object with expected output values

## Architecture

The simulator consists of four main components:

1. **SystemVerilogParser**: Parses `.sv` files and extracts module information
2. **LogicEvaluator**: Evaluates logic expressions for given input values
3. **TruthTableGenerator**: Generates and displays truth tables
4. **TestRunner**: Runs JSON test cases and reports results

## Examples

See the included example files:
- `nand_gate.sv`: Simple NAND gate implementation
- `inverter.sv`: Inverter built from NAND gate instantiation
- `and_gate.sv`: AND gate built from NAND gate and inverter modules
- `or_gate.sv`: OR gate built using De Morgan's law with inverters + NAND
- `half_adder.sv`: Half adder with XOR sum and AND carry logic
- `full_adder.sv`: Full adder built from two half adders with carry chain
- `alu_1bit.sv`: 1-bit ALU slice with 8 operations (AND, OR, XOR, ADD, SUB, NOT, PASS)
- `complex_logic.sv`: Multi-output module with various operations
- `tests_nand_gate.json`: Test cases for the NAND gate
- `tests_inverter.json`: Test cases for the inverter
- `tests_and_gate.json`: Test cases for the AND gate
- `tests_or_gate.json`: Test cases for the OR gate
- `tests_half_adder.json`: Test cases for the half adder
- `tests_full_adder.json`: Test cases for the full adder
- `tests_alu_1bit.json`: Test cases for the 1-bit ALU

## Limitations

This is an MVP focused on basic combinational logic. Current limitations include:

- No sequential logic (flip-flops, latches)
- No multi-bit vectors (only scalar signals)
- Limited to basic bitwise operations
- No arithmetic operators (+, -, *, /)
- Module instantiation supports only same-directory modules

## Future Enhancements

Potential areas for expansion:
- Multi-bit vector support
- Sequential logic elements
- Module hierarchy and instantiation
- More operators (arithmetic, comparison, shift)
- Behavioral modeling support
- Timing simulation

## License

This code is designed for commercial game development and can be redistributed as needed.