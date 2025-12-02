# PySVSim - SystemVerilog Simulator

A pure Python SystemVerilog simulator designed for educational game development. Write hardware modules in SystemVerilog, generate truth tables, visualize waveforms, and validate designs against test cases.

## Features

### Core Simulation
- **Pure Python**: Uses matplotlib for visualization, no other external dependencies
- **Bus Support**: Full support for multi-bit buses with clean notation (e.g., `input [3:0] data`)
- **Hierarchical Design**: Module instantiation with bit selection (e.g., `.A(data[0])`)
- **Combinational Logic**: Handles bitwise operations (`&`, `|`, `^`, `~`)
- **Sequential Logic**: Supports `always_ff` blocks, registers, counters with clock/enable/reset
- **NAND Gate Analysis**: Counts NAND gates in hierarchical designs for complexity analysis

### Testing & Visualization
- **Truth Table Generation**: Automatic truth tables for combinational logic (configurable limit)
- **Waveform Generation**: Professional timing diagrams for sequential logic testing
- **Image Output**: PNG images of truth tables and waveforms for game integration
- **JSON Testing**: Validate designs with custom test cases (combinational and sequential)
- **Parallel Test Runner**: Multi-core regression testing with detailed reports
- **Game-Ready**: Designed to be easily embedded in larger Python games

## Usage

### Basic Simulation

```bash
# Generate truth table for a module
python pysvsim.py --file parts/and_gate.sv

# Simulate with test cases
python pysvsim.py --file parts/full_adder.sv --test parts/full_adder.json
```

### Test Runner

```bash
# Test a single file (outputs truth table/waveform + test results)
python test_runner.py parts/and_gate.sv

# Test entire directory with parallel processing
python test_runner.py parts/

# Save results to file
python test_runner.py parts/ > test_results.txt
```

### Batch Testing

```bash
# Run all tests and save reports
test.bat
```

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

### Combinational Logic Tests
```json
[
    {"inA": 0, "inB": 0, "expect": {"outY": 1}},
    {"inA": 0, "inB": 1, "expect": {"outY": 1}},
    {"inA": 1, "inB": 0, "expect": {"outY": 1}},
    {"inA": 1, "inB": 1, "expect": {"outY": 0}}
]
```

### Sequential Logic Tests
```json
{
    "sequential": true,
    "test_cases": [
        {
            "name": "Reset behavior",
            "sequence": [
                {"inputs": {"clk": 1, "reset": 1, "enable": 0}, "expected": {"count": 0}},
                {"inputs": {"clk": 1, "reset": 0, "enable": 1}, "expected": {"count": 1}}
            ]
        }
    ]
}
```

## SystemVerilog Support

### Combinational Logic
- **Module declarations** with input/output ports (single-bit and multi-bit buses)
- **Bus declarations**: `input [3:0] A`, `output [7:0] result`, `wire [3:0] temp`
- **Bit selection**: `A[2]`, `data[0]`, `bus[7:4]`
- **Concatenation**: `{a, b, c}`, `{4{bit}}` (replication)
- **Module instantiation** with hierarchical connections and bit selection
- **Bitwise operators**: `&`, `|`, `^`, `~`
- **Literals**: `1'b0`, `8'hFF`, `4'd10`

### Sequential Logic
- **always_ff blocks**: `always_ff @(posedge clk)`
- **Conditional assignments**: `if/else if/else` chains
- **Arithmetic in sequential**: `count <= count + 1`
- **Clock, enable, reset** signals

### Example Combinational Module
```verilog path=null start=null
module nand_gate (
    input inA,
    input inB,
    output outY
);
    assign outY = ~(inA & inB);
endmodule
```

### Example Sequential Module
```verilog path=null start=null
module counter8 (
    input clk,
    input reset,
    input enable,
    output reg [7:0] count
);
    always_ff @(posedge clk) begin
        if (reset)
            count <= 8'b0;
        else if (enable)
            count <= count + 1;
    end
endmodule
```

## Architecture

The simulator consists of five main components:

1. **SystemVerilogParser**: Parses `.sv` files, extracts module info, buses, and sequential blocks
2. **LogicEvaluator**: Evaluates combinational logic with bus support and NAND gate counting
3. **SequentialLogicEvaluator**: Evaluates sequential logic with state management
4. **TruthTableGenerator**: Generates truth tables for combinational modules
5. **TestRunner**: Parallel test execution with truth table/waveform output

## Module Library

The `parts/` directory contains a comprehensive library of verified modules:

### Logic Gates (1-bit and 8-bit variants)
- NAND, AND, OR, NOR, XOR, XNOR, NOT gates
- All built hierarchically from NAND gates

### Arithmetic
- Half adder, Full adder (15 NANDs)
- Ripple-carry adders: 4/8/16/32/64-bit
- Carry-select adders: 8/16/32/64-bit (faster hardware, slower simulation)

### Data Path
- 2:1 Multiplexers: 1/4/8/16/32-bit
- Registers: 1/8/16/32/64-bit with clock/enable
- 8-bit counter with reset/enable

### NAND Gate Counts
- Full adder: 15 NANDs
- 4-bit adder: 60 NANDs
- 8-bit adder: 120 NANDs
- 32-bit ripple-carry: 480 NANDs
- 32-bit carry-select: 2,332 NANDs

## Directory Structure

```
pysvsim/
├── pysvsim.py          # Main simulator
├── test_runner.py      # Parallel test runner
├── test.bat            # Batch test script
├── parts/              # Verified module library
│   ├── *.sv            # SystemVerilog modules
│   └── *.json          # Test cases
├── testing/            # Additional test modules
├── roms/               # ROM data files
└── goals/              # Project milestones
```

## Current Limitations

- **Arithmetic operators**: Only in sequential blocks (combinational uses adder modules)
- **Same-directory modules**: Modules must be in same directory as parent
- **No timing**: Pure functional simulation without propagation delays
- **Memory arrays**: Not yet supported (planned for CPU milestone)

## Roadmap

See `goals/` for detailed milestone documents:

- **8-bit CPU**: Simple CPU with ROM/RAM support (`8bitcpu-milestone.md`)
- **RV32I CPU**: Full RISC-V implementation with serial I/O (`rv32i-milestone.md`)
