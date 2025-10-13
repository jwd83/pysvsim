# SystemVerilog Simulator

A pure Python SystemVerilog simulator designed for game development. Players can write small hardware modules in SystemVerilog, and the simulator generates truth tables and validates designs against test cases.

## Features

- **Pure Python**: No external dependencies except standard libraries
- **Combinational Logic Support**: Handles basic logic operations (`&`, `|`, `^`, `~`)
- **Truth Table Generation**: Automatically generates truth tables for up to 16 input combinations
- **JSON Testing**: Validate designs with custom test cases
- **Game-Ready**: Designed to be easily embedded in larger Python games

## Usage

### Basic Truth Table Generation

```bash
python sv_simulator.py --file nand_gate.sv
```

### With Custom Test Cases

```bash
python sv_simulator.py --file nand_gate.sv --test tests.json
```

### Limit Input Combinations

```bash
python sv_simulator.py --file complex_logic.sv --max-combinations 4
```

## Command Line Arguments

- `--file <verilog_file>`: SystemVerilog file to simulate (required)
- `--test <json_file>`: JSON test file (optional)
- `--max-combinations N`: Maximum number of input combinations to test (default: 16)

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
- `complex_logic.sv`: Multi-output module with various operations
- `tests.json`: Example test cases for the NAND gate
- `inverter_tests.json`: Test cases for the inverter
- `and_gate_tests.json`: Test cases for the AND gate

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