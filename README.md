# SystemVerilog Simulator

A pure Python SystemVerilog simulator designed for game development. Players can write small hardware modules in SystemVerilog, and the simulator generates truth tables and validates designs against test cases.

## Features

- **Pure Python**: No external dependencies except standard libraries
- **Bus Support**: Full support for multi-bit buses with clean notation (e.g., `input [3:0] data`)
- **Hierarchical Design**: Module instantiation with bit selection (e.g., `.A(data[0])`)
- **Combinational Logic Support**: Handles basic logic operations (`&`, `|`, `^`, `~`)
- **NAND Gate Analysis**: Counts NAND gates used in hierarchical designs for complexity analysis
- **Truth Table Generation**: Automatically generates truth tables for up to 256 input combinations
- **JSON Testing**: Validate designs with custom test cases using integer bus values
- **Comprehensive Test Suite**: Built-in test runner with detailed reports and regression testing
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

### Bus-based Design with Limited Combinations

```bash
python pysvsim.py --file adder_4bit_bus.sv --test tests_adder_4bit_bus.json --max-combinations 64
```

### Test Runner - Individual Files

```bash
# Test a single SystemVerilog file
python test_runner.py testing/005-Notgate.sv

# Test with verbose output and NAND gate counts
python test_runner.py testing/008-Xorgate.sv --verbose
```

### Test Runner - Directory Testing

```bash
# Test entire directory
python test_runner.py testing/

# Test directory with detailed reports
python test_runner.py testing/ --detailed-report

# Skip truth tables, only run JSON tests
python test_runner.py testing/ --summary-only
```

## Command Line Arguments

### `pysvsim.py` Arguments

- `--file <verilog_file>`: SystemVerilog file to simulate (required)
- `--test <json_file>`: JSON test file (optional)
- `--max-combinations N`: Maximum number of input combinations to test (default: 256)

### `test_runner.py` Arguments

- `path`: SystemVerilog file or directory to test (required)
- `--max-combinations N`: Maximum truth table combinations (default: 256)
- `--verbose, -v`: Enable detailed progress information with NAND gate counts
- `--summary-only`: Skip truth table generation, only run JSON tests
- `--continue-on-error`: Continue when files fail (default: True)
- `--stop-on-first-error`: Stop on first error
- `--detailed-report`: Show comprehensive report with truth tables

## Test File Structure

The test runner expects JSON test files with the same base name as the SystemVerilog file:

```
testing/
├── 005-Notgate.sv      # SystemVerilog module
├── 005-Notgate.json    # JSON test cases
├── 012-Vector1.sv      # Another module
└── 012-Vector1.json    # Its test cases
```

## JSON Test Format

```json
[
    {
        "input1": value1,
        "input2": value2,
        "expect": {
            "output1": expected1,
            "output2": expected2
        }
    }
]
```

Each test case contains:
- **Input values**: All inputs must be specified (integers for buses, 0/1 for single bits)
- **Expected outputs**: `expect` object with expected output values

## SystemVerilog Support

### Currently Supported
- **Module declarations** with input/output ports (single-bit and multi-bit buses)
- **Bus declarations**: `input [3:0] A`, `output [7:0] result`, `wire [3:0] temp`
- **Bit selection**: Individual bit access like `A[2]`, `data[0]` in expressions
- **Bus assignments**: Direct bus-to-bus assignments like `assign Y = A`
- **Module instantiation** with hierarchical connections and bit selection
- **Bitwise operators**: `&` (AND), `|` (OR), `^` (XOR), `~` (NOT)
- **Expression grouping** with parentheses
- **Mixed bus/scalar designs**: Combine buses and single-bit signals seamlessly

### Example SystemVerilog Module (Single-bit)

```verilog
module nand_gate (
    input inA,
    input inB,
    output outY
);
    assign outY = ~(inA & inB);
endmodule
```

### Bus-based Module Example

```verilog
module adder_4bit_bus (
    input [3:0] A,      // 4-bit input bus A
    input [3:0] B,      // 4-bit input bus B
    input Cin,          // Single-bit carry input
    output [3:0] Sum,   // 4-bit sum output bus
    output Cout         // Single-bit carry output
);
    // Internal carry wires
    wire C1, C2, C3;
    
    // Instantiate full adders with bit selection
    full_adder fa0 (.A(A[0]), .B(B[0]), .Cin(Cin), .Sum(Sum[0]), .Cout(C1));
    full_adder fa1 (.A(A[1]), .B(B[1]), .Cin(C1),  .Sum(Sum[1]), .Cout(C2));
    full_adder fa2 (.A(A[2]), .B(B[2]), .Cin(C2),  .Sum(Sum[2]), .Cout(C3));
    full_adder fa3 (.A(A[3]), .B(B[3]), .Cin(C3),  .Sum(Sum[3]), .Cout(Cout));
endmodule
```

## Architecture

The simulator consists of four main components:

1. **SystemVerilogParser**: Parses `.sv` files and extracts module information including bus declarations
2. **LogicEvaluator**: Evaluates logic expressions with full bus support, bit selection, and NAND gate counting
3. **TruthTableGenerator**: Generates truth tables with clean bus notation (e.g., `A[3:0] = 5`)
4. **TestRunner**: Comprehensive regression test suite with detailed reports

## Examples

See the included example files:

### SystemVerilog Modules
- `nand_gate.sv`: Simple NAND gate implementation
- `inverter.sv`: Inverter built from NAND gate instantiation (1 NAND)
- `and_gate.sv`: AND gate built from NAND gate and inverter modules (2 NANDs)
- `or_gate.sv`: OR gate built using De Morgan's law with inverters + NAND (3 NANDs)
- `xor_gate.sv`: XOR gate built using (A & ~B) | (~A & B) with AND/OR/inverter modules
- `nor_gate.sv`: NOR gate built using OR gate + inverter (NOT OR)
- `half_adder.sv`: Half adder built from XOR and AND gate modules
- `full_adder.sv`: Full adder built from two half adders with carry chain (15 NANDs)
- `adder_4bit_bus.sv`: **4-bit adder using proper bus notation** (60 NANDs)
- `adder_16bit.sv`: **16-bit adder using hierarchical 4-bit adders** (240 NANDs)

### Testing Directory Structure
- `testing/`: Contains SystemVerilog files with matching JSON test cases
- `parts/`: Additional example modules with hierarchical designs

## Limitations

This simulator focuses on combinational logic suitable for educational games. Current limitations include:

- **No sequential logic** (flip-flops, latches, clocked circuits)
- **Basic bitwise operations only** (no arithmetic operators like +, -, *, /)
- **Same-directory module loading** (no complex module hierarchy paths)
- **Combinational logic only** (no behavioral modeling or timing)

## Future Enhancements

Potential areas for expansion:
- **Sequential logic elements** (D flip-flops, counters, state machines)
- **Arithmetic operators** (+, -, *, /) for more complex designs
- **Advanced bus operations** (concatenation, slicing, shifting)
- **Behavioral modeling** support (`always` blocks, `if`/`case` statements)
- **Timing simulation** and clock domain analysis
- **Memory elements** (ROMs, RAMs, register files)
