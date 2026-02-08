# PySVSim - SystemVerilog Simulator

A pure Python SystemVerilog simulator designed for an educational digital logic game. Players design hardware modules from NAND gates up to CPUs. The simulator parses SystemVerilog, evaluates logic, generates truth tables/waveforms, and validates designs against test cases.

## Project Status

**Current State: Core simulator stable, working toward 8-bit CPU milestone**

| Metric | Value |
|--------|-------|
| Last Verified | February 8, 2026 |
| `parts/` Regression | 36/36 files passing, 316/316 test cases |
| `testing/` Regression | 40/40 files passing, 261/261 test cases |
| Combined Regression | 76 files passing, 577/577 test cases |
| Total NAND Gates (`parts/`) | 13,092 |

## Features

### Core Simulation
- **Pure Python**: Single direct dependency (`matplotlib`) for visualization
- **Bus Support**: Multi-bit buses with clean notation (`input [7:0] data`)
- **Hierarchical Design**: Module instantiation with bit selection (`.A(data[0])`)
- **Combinational Logic**: Bitwise operators (`&`, `|`, `^`, `~`)
- **Sequential Logic**: `always_ff` blocks, registers, counters with clock/enable/reset
- **Sequential AST Execution**: `if/else`, `case/default`, blocking/nonblocking assignment semantics
- **Memory Arrays**: `reg/logic [W] mem [D]` read/write support for ROM/RAM-style modules
- **NAND Gate Analysis**: Counts NAND gates in hierarchical designs for complexity scoring

### Testing & Visualization
- **Truth Table Generation**: Automatic truth tables for combinational logic
- **Waveform Generation**: Timing diagrams for sequential logic
- **Image Output**: PNG images for game integration
- **JSON Testing**: Test cases for combinational and sequential designs
- **Parallel Test Runner**: Multi-core regression testing

## Quick Start

```bash
# Generate truth table for a module
uv run pysvsim.py --file parts/and_gate.sv

# Run with test cases
uv run pysvsim.py --file parts/full_adder.sv --test parts/full_adder.json

# Test a single file
uv run test_runner.py parts/and_gate.sv

# Test entire directory (parallel)
uv run test_runner.py parts/
uv run test_runner.py testing/

# Batch test (Windows)
test.bat
```

## Module Library (`parts/`)

All modules are built hierarchically from NAND gates.

### Logic Gates
| Module | 1-bit | 8-bit |
|--------|-------|-------|
| NAND | `nand_gate.sv` | `nand_gate_8bit.sv` |
| AND | `and_gate.sv` | `and_gate_8bit.sv` |
| OR | `or_gate.sv` | `or_gate_8bit.sv` |
| NOR | `nor_gate.sv` | `nor_gate_8bit.sv` |
| XOR | `xor_gate.sv` | `xor_gate_8bit.sv` |
| XNOR | `xnor_gate.sv` | `xnor_gate_8bit.sv` |
| NOT | `not_gate.sv` | `not_gate_8bit.sv` |

### Arithmetic
| Module | NAND Gates |
|--------|------------|
| Half Adder | 6 |
| Full Adder | 15 |
| 4-bit Adder | 60 |
| 8-bit Adder | 120 |
| 16-bit Adder | 240 |
| 32-bit Adder | 480 |
| 64-bit Adder | 960 |
| 8-bit Carry-Select | 220 |
| 16-bit Carry-Select | 732 |
| 32-bit Carry-Select | 2,332 |
| 64-bit Carry-Select | 7,260 |

### Data Path
| Module | Variants |
|--------|----------|
| 2:1 Mux | 1, 4, 8, 16, 32-bit |
| Register | 1, 8, 16, 32, 64-bit |
| Counter | 8-bit with reset/enable |

## Test File Format

JSON test files share the same base name as the SystemVerilog file.

### Combinational
```json
[
    {"inA": 0, "inB": 0, "expect": {"outY": 1}},
    {"inA": 1, "inB": 1, "expect": {"outY": 0}}
]
```

### Sequential
```json
{
    "sequential": true,
    "memory_files": {
        "rom": [
            {
                "module": "memory_cpu_stub",
                "memory": "rom",
                "file": "memory_cpu_stub_rom.txt"
            }
        ],
        "ram": [
            {
                "module": "memory_cpu_stub",
                "memory": "ram",
                "file": "memory_cpu_stub_ram.txt"
            }
        ]
    },
    "test_cases": [
        {
            "name": "Reset behavior",
            "sequence": [
                {"inputs": {"clk": 1, "reset": 1}, "expected": {"count": 0}},
                {"inputs": {"clk": 1, "reset": 0, "enable": 1}, "expected": {"count": 1}}
            ]
        }
    ]
}
```

## SystemVerilog Support

### Supported
- Module declarations with input/output ports
- Buses: `input [7:0] A`, `wire [3:0] temp`
- Bit selection: `A[2]`, `bus[7:4]`
- Concatenation: `{a, b}`, `{4{bit}}`
- Bitwise operators: `&`, `|`, `^`, `~`
- Literals: `1'b0`, `8'hFF`, `4'd10`
- Keywords: `logic`, `reg`, `signed`, `unsigned`
- `always_ff @(posedge clk)` blocks
- `if/else` and `case/default` in sequential blocks
- Blocking (`=`) and nonblocking (`<=`) assignment execution in sequential AST
- Arithmetic in sequential blocks: `count + 1`
- Memory arrays: `reg [7:0] memory [255:0]`

### Limitations
- Arithmetic only in sequential blocks (combinational uses adder modules)
- Modules must be in same directory as parent
- No timing/propagation delays
- No event-driven timing wheel (cycle-based sequential stepping only)

## Directory Structure

```
pysvsim/
├── pysvsim.py          # Main simulator
├── test_runner.py      # Parallel test runner
├── parts/              # 36 verified library modules
├── testing/            # 40 HDLBits/validation modules
├── roms/               # ROM data files (for CPU)
└── goals/              # Milestone documents
```

## Next Steps: 8-bit CPU

The next milestone is a simple 8-bit CPU. See `goals/8bitcpu-milestone.md` for details.

### Required Modules
1. **Program Counter** - 8-bit counter with load for jumps
2. **Register File** - 8 registers x 8 bits with dual read
3. **ALU** - 8-bit with ADD, SUB, AND, OR, XOR, NOT, PASS
4. **Instruction Decoder** - Decodes 8-bit instructions to control signals
5. **Status Register** - Zero, Carry, Negative flags
6. **ROM Module** - Instruction memory interface
7. **RAM Module** - Data memory (256 bytes)

### Simulator Enhancements Needed
1. **Extended CPU Programs** - Broader instruction coverage and longer traces
2. **I/O Peripherals** - Memory-mapped serial/timer-style modules
3. **Extended Testing** - Program-level regression sets

## Future Roadmap

- **8-bit CPU** - Simple CPU with ROM/RAM (`goals/8bitcpu-milestone.md`)
- **RV32I CPU** - Full RISC-V implementation (`goals/rv32i-milestone.md`)
