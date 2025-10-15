# SystemVerilog Simulator

A pure Python SystemVerilog simulator designed for game development. Players can write small hardware modules in SystemVerilog, and the simulator generates truth tables and validates designs against test cases.

## Features

- **Pure Python**: No external dependencies except standard libraries
- **Bus Support**: Full support for multi-bit buses with clean notation (e.g., `input [3:0] data`)
- **Hierarchical Design**: Module instantiation with bit selection (e.g., `.A(data[0])`)
- **Combinational Logic Support**: Handles basic logic operations (`&`, `|`, `^`, `~`)
- **Truth Table Generation**: Automatically generates truth tables for up to 256 input combinations
- **JSON Testing**: Validate designs with custom test cases using integer bus values
- **Comprehensive Test Suite**: Built-in test runner with detailed reports
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

### Run Comprehensive Test Suite

```bash
python test.py
```

### Batch Testing with `testfolder.py`

```bash
# Test all .sv files in a directory recursively
python testfolder.py ./tmp

# Show detailed results with full truth tables and error information
python testfolder.py ./tmp --verbose

# Quick summary statistics only
python testfolder.py ./tmp --summary-only

# Limit test combinations and stop on first error for debugging
python testfolder.py ./tmp --max-combinations 16 --stop-on-error --verbose
```

## Command Line Arguments

### `pysvsim.py` Arguments

- `--file <verilog_file>`: SystemVerilog file to simulate (required)
- `--test <json_file>`: JSON test file (optional)
- `--max-combinations N`: Maximum number of input combinations to test (default: 256)

### `testfolder.py` Arguments

- `directory`: Directory to search for .sv files recursively (required)
- `--max-combinations N`: Maximum number of input combinations per file (default: 64)
- `--verbose`: Show detailed output including full truth tables and error information
- `--summary-only`: Only show summary statistics, not individual test results
- `--continue-on-error`: Continue testing other files even if some fail (default: True)
- `--stop-on-error`: Stop testing when the first error occurs

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

### Mixed Bus/Scalar Example

```verilog
module parity_checker (
    input [2:0] data,    // 3-bit bus input
    input enable,        // Single-bit enable
    output [2:0] output_data, // Bus passthrough
    output parity        // Calculated parity bit
);
    assign output_data = data;
    assign parity = enable ? (data[2] ^ data[1] ^ data[0]) : 1'b0;
endmodule
```

## Test File Format

Test cases are specified in JSON format with support for both single-bit and bus values.

### Single-bit Test Example

```json
[
  {"inA": 0, "inB": 0, "expect": {"outY": 1}},
  {"inA": 0, "inB": 1, "expect": {"outY": 1}},
  {"inA": 1, "inB": 0, "expect": {"outY": 1}},
  {"inA": 1, "inB": 1, "expect": {"outY": 0}}
]
```

### Bus-based Test Example

```json
[
  {"A": 0, "B": 0, "Cin": 0, "expect": {"Sum": 0, "Cout": 0}},
  {"A": 5, "B": 10, "Cin": 0, "expect": {"Sum": 15, "Cout": 0}},
  {"A": 15, "B": 1, "Cin": 0, "expect": {"Sum": 0, "Cout": 1}},
  {"A": 7, "B": 9, "Cin": 0, "expect": {"Sum": 0, "Cout": 1}}
]
```

Each test case contains:
- **Input values**: All inputs must be specified (integers for buses, 0/1 for single bits)
- **Expected outputs**: `expect` object with expected output values

## Testing Scripts

The simulator includes comprehensive testing tools for both individual files and batch processing:

### `test.py` - Comprehensive Test Suite

Runs all predefined tests and generates detailed reports:

```bash
python test.py
```

**Features:**
- Tests all included SystemVerilog modules with their corresponding JSON test files
- Generates truth tables for each module
- Creates a detailed `report.md` file with test results
- Shows success/failure statistics
- Includes full verbosity with no truth table truncation

### `testfolder.py` - Recursive Directory Testing

Recursively tests all `.sv` files in a directory structure:

```bash
python testfolder.py <directory> [options]
```

**Key Features:**
- **Recursive Discovery**: Automatically finds all `.sv` files in subdirectories
- **Batch Processing**: Tests hundreds of files efficiently with timeouts
- **Detailed Truth Tables**: Shows complete truth tables for successful tests (with `--verbose`)
- **Comprehensive Error Reporting**: Shows full parsing output and error context for failures
- **Success Rate Analysis**: Provides statistics on supported vs unsupported SystemVerilog features
- **Flexible Output**: Summary-only mode or detailed verbose output

**Example Output - Successful Test:**
```
[PASS] (0.05s) - Inputs: 3, Outputs: 4

Truth Table:
     a      b      c |      w      x      y      z
--------------------------------------------------
     0      0      0 |      0      0      0      0
     0      0      1 |      0      0      0      1
     0      1      0 |      0      1      1      0
     [... complete truth table ...]
```

**Example Output - Failed Test:**
```
[FAIL] (0.05s)
Error: Error: 'reg out_alwaysblock'
Full output:
  Parsing SystemVerilog file: procedures/029-AlwaysBlocks.sv
  Module: top_module
  Inputs: ['a', 'b']
  Outputs: ['out_assign', 'reg out_alwaysblock']
  Error: 'reg out_alwaysblock'  # Shows exactly where parsing failed
```

**Use Cases:**
- **HDL Course Validation**: Test homework solutions from courses like HDLBits
- **Simulator Development**: Validate parser improvements and feature additions
- **Educational Assessment**: Quickly assess which SystemVerilog constructs are supported
- **Debugging**: Identify specific parsing failures and unsupported syntax

**Typical Success Rates:**
- **Basic Combinational Logic**: 90-100% (simple gates, multiplexers, decoders)
- **Intermediate Combinational**: 70-85% (complex expressions, buses, arithmetic)
- **Sequential Logic**: 0-10% (uses `reg`, `always` - not supported yet)
- **Module Hierarchies**: Variable (depends on external module availability)

**Example Usage:**
```bash
# Test HDLBits homework solutions with verbose output
python testfolder.py ./hdlbits_solutions --verbose --max-combinations 32

# Quick assessment of a large codebase
python testfolder.py ./verilog_designs --summary-only

# Debug specific parsing issues
python testfolder.py ./problematic_files --verbose --stop-on-error
```

## Architecture

The simulator consists of four main components:

1. **SystemVerilogParser**: Parses `.sv` files and extracts module information including bus declarations
2. **LogicEvaluator**: Evaluates logic expressions with full bus support and bit selection
3. **TruthTableGenerator**: Generates truth tables with clean bus notation (e.g., `A[3:0] = 5`)
4. **TestRunner**: Comprehensive test suite with detailed Markdown reports

## Examples

See the included example files:

### SystemVerilog Modules
- `nand_gate.sv`: Simple NAND gate implementation
- `inverter.sv`: Inverter built from NAND gate instantiation
- `and_gate.sv`: AND gate built from NAND gate and inverter modules
- `or_gate.sv`: OR gate built using De Morgan's law with inverters + NAND
- `xor_gate.sv`: XOR gate built using (A & ~B) | (~A & B) with AND/OR/inverter modules
- `nor_gate.sv`: NOR gate built using OR gate + inverter (NOT OR)
- `half_adder.sv`: Half adder built from XOR and AND gate modules
- `full_adder.sv`: Full adder built from two half adders with carry chain
- `alu_1bit.sv`: Hierarchical 1-bit ALU with 4 operations (AND, OR, XOR, ADD)
- `adder_4bit_bus.sv`: **4-bit adder using proper bus notation** - demonstrates modern SystemVerilog design
- `mux_4to1.sv`: **4:1 multiplexer with bus inputs** - hierarchical design using decoders and select logic

### JSON Test Files
- `tests_*.json`: Comprehensive test cases for all modules with full input coverage

### Testing Scripts
- `test.py`: **Automated test runner** - runs all predefined tests and generates detailed reports
- `testfolder.py`: **Batch testing tool** - recursively tests all .sv files in a directory with detailed output
- `report.md`: Generated test report with truth tables and pass/fail status

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
