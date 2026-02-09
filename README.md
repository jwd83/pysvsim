# PySVSim - SystemVerilog Simulator

A pure Python SystemVerilog simulator designed for an educational digital logic game. Players design hardware modules from NAND gates up to CPUs. The simulator parses SystemVerilog, evaluates logic, generates truth tables/waveforms, and validates designs against test cases.

## Project Status

**Current State: Core simulator stable, Overture CPU core implemented and validated**

| Metric | Value |
|--------|-------|
| Last Verified | February 9, 2026 |
| `parts/` Regression | 74/74 files passing, 678/678 test cases |
| `testing/` Regression | 40/40 files passing, 261/261 test cases |
| Combined Regression | 114 files passing, 939/939 test cases |
| Overture ROM ISA Suites | ALU smoke, branch, and I/O programs passing |
| Total NAND Gates (`parts/`) | 16,735 |

## Features

### Core Simulation
- **Pure Python**: Single direct dependency (`matplotlib`) for visualization
- **Bus Support**: Multi-bit buses with clean notation (`input [7:0] data`)
- **Hierarchical Design**: Module instantiation with bit selection (`.A(data[0])`)
- **Combinational Logic**: Bitwise operators (`&`, `|`, `^`, `~`), arithmetic (`+`, `-`, `*`), ternary operator (`sel ? a : b`)
- **`always_comb` Blocks**: Full combinational procedural blocks with `if/else` and `case/default`
- **Sequential Logic**: `always_ff` blocks, registers, counters with clock/enable/reset
- **Sequential AST Execution**: `if/else`, `case/default`, blocking/nonblocking assignment semantics
- **ROM Primitives**: Modules named `rom_*` auto-load data files by naming convention
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
| 4:1 Mux | 8-bit (gate-level), 8-bit (`always_comb`) |
| 8:1 Mux | 8-bit |
| Ternary Mux | 8-bit (ternary operator) |
| Decoder | 3-to-8 |
| Register | 1, 8, 16, 32, 64-bit |
| Register File | 8x8 (dual read ports) |
| Counter | 8-bit with reset/enable |
| ALU | 8-bit (`always_comb`, 4 ops: AND, OR, XOR, NOT) |

### ROM Primitives
| Module | Description |
|--------|-------------|
| `rom_deadbeef` | 4x8 ROM (demo) |

ROM modules use a naming convention: `rom_{name}` auto-loads `{name}.txt`. See [ROM Primitives](#rom-primitives-1) below.

### Overture CPU (`parts/overture/`)
- `overture_cpu.sv`: 8-bit Overture ISA executor (`Immediate`, `Calculate`, `Copy`, `Condition`)
- `overture_alu_8bit.sv`: OR/NAND/NOR/AND/ADD/SUB ALU
- `overture_decoder_8bit.sv`: instruction field decoder
- `overture_pc_8bit.sv`: 8-bit program counter with jump/load behavior
- ROM test programs:
  - `overture_prog_alu.txt`
  - `overture_prog_branch.txt`
  - `overture_prog_io.txt`
- Validation JSONs:
  - `overture_cpu.json`
  - `overture_cpu_program_branch.json`
  - `overture_cpu_program_io.json`

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
- Arithmetic in assign statements: `+`, `-`, `*`
- Ternary operator: `assign out = sel ? a : b` (nested right-associative)
- Literals: `1'b0`, `8'hFF`, `4'd10`
- Keywords: `logic`, `reg`, `signed`, `unsigned`
- `always_comb` blocks with `if/else` and `case/default`
- `always_ff @(posedge clk)` blocks
- `if/else` and `case/default` in sequential blocks
- Blocking (`=`) and nonblocking (`<=`) assignment execution
- Arithmetic in sequential blocks: `count + 1`
- Memory arrays: `reg [7:0] memory [255:0]`
- ROM primitives: `rom_*` modules auto-load data files

### Limitations
- Modules must be in same directory as parent
- No timing/propagation delays
- No event-driven timing wheel (cycle-based sequential stepping only)

### ROM Primitives

Modules with a `rom_` prefix are treated as built-in ROM primitives. The SV file only needs to declare the interface -- the simulator handles data loading automatically.

- **Naming convention**: `rom_{name}` loads `{name}.txt` (e.g., `rom_deadbeef` loads `deadbeef.txt`)
- **Data file search order**: SV file directory, then `roms/` subdirectory, then `roms/` relative to CWD
- **Data format**: One binary value per line (e.g., `11011110`), supports `#`/`//` comments

## Directory Structure

```
pysvsim/
├── pysvsim.py          # Main simulator
├── test_runner.py      # Parallel test runner
├── parts/              # 74 verified library modules (includes overture CPU workspace)
├── testing/            # 40 HDLBits/validation modules
├── roms/               # ROM data files (for CPU)
└── goals/              # Milestone documents
```

## Goal Readiness

Three progressive CPU milestones. See `goals/` for detailed plans.

| | Goal 1: Overture | Goal 2: LEG | Goal 3: RV32I |
|---|---|---|---|
| **Description** | 8-bit CPU, 8-bit instructions | 8-bit CPU, 32-bit instructions | 32-bit RISC-V CPU |
| **Reference** | `goal-1-overture_cpu_isa_reference.md` | `goal-2-advanced-8bitcpu-milestone.md` | `goal-3-rv32i-milestone.md` |

✅ = ready, ❌ = needed but not built yet, ➖ = not needed

### Simulator Features

| Feature | Have | Goal 1 | Goal 2 | Goal 3 |
|---------|:----:|:------:|:------:|:------:|
| Combinational logic | ✅ | ✅ | ✅ | ✅ |
| Sequential logic (`always_ff`) | ✅ | ✅ | ✅ | ✅ |
| `always_comb` blocks | ✅ | ✅ | ✅ | ✅ |
| Ternary operator | ✅ | ✅ | ✅ | ✅ |
| ROM primitives | ✅ | ✅ | ✅ | ✅ |
| Memory arrays (RAM) | ✅ | ➖ | ✅ | ✅ |
| Hierarchical instantiation | ✅ | ✅ | ✅ | ✅ |
| Memory-mapped I/O | ❌ | ❌ | ➖ | ❌ |
| UART / serial I/O | ❌ | ➖ | ➖ | ❌ |

### Hardware Modules (`parts/`)

| Module | Have | Goal 1 | Goal 2 | Goal 3 |
|--------|:----:|:------:|:------:|:------:|
| Logic gates (1-bit, 8-bit) | ✅ | ✅ | ✅ | ✅ |
| Adders (up to 64-bit) | ✅ | ✅ | ✅ | ✅ |
| Muxes (2:1 up to 32-bit) | ✅ | ✅ | ✅ | ✅ |
| Muxes (4:1, 8:1) | ✅ | ✅ | ✅ | ✅ |
| Decoder (3-to-8) | ✅ | ✅ | ✅ | ✅ |
| Registers (1 to 64-bit) | ✅ | ✅ | ✅ | ✅ |
| Register file (8x8) | ✅ | ✅ | ✅ | ➖ |
| Register file (32x32) | ❌ | ➖ | ➖ | ❌ |
| Counter (8-bit) | ✅ | ✅ | ✅ | ➖ |
| ALU (8-bit, basic) | ✅ | ✅ | ✅ | ➖ |
| ALU (Overture: OR/NAND/NOR/AND/ADD/SUB) | ✅ | ✅ | ➖ | ➖ |
| ALU (32-bit, RV32I ops) | ❌ | ➖ | ➖ | ❌ |
| Program counter (with jump/load) | ✅ | ✅ | ✅ | ❌ |
| Instruction decoder | ✅ | ✅ | ✅ | ❌ |
| Overture CPU core (8-bit ISA + ROM fetch) | ✅ | ✅ | ➖ | ➖ |
| Status/flags register | ❌ | ➖ | ❌ | ❌ |
| RAM module | ❌ | ➖ | ❌ | ❌ |
| ROM (data) | ✅ | ✅ | ✅ | ✅ |
| I/O ports | ✅ | ✅ | ➖ | ❌ |
| Comparator (32-bit) | ❌ | ➖ | ➖ | ❌ |
| Barrel shifter | ❌ | ➖ | ➖ | ❌ |
| Immediate generator | ❌ | ➖ | ➖ | ❌ |
