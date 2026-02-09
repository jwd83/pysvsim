# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PySVSim is a pure Python SystemVerilog simulator for an educational digital logic game. Players design hardware modules from NAND gates up to CPUs. The simulator parses SystemVerilog, evaluates logic, generates truth tables/waveforms, and validates designs against test cases.

## Commands

Use `uv` to manage dependencies and run Python:

```bash
# Test a single module
uv run test_runner.py parts/and_gate.sv

# Test entire directory (parallel execution)
uv run test_runner.py parts/
uv run test_runner.py testing/

# Generate truth table / run simulation
uv run pysvsim.py --file parts/full_adder.sv
uv run pysvsim.py --file parts/full_adder.sv --test parts/full_adder.json

# Add a dependency
uv add <package>
```

## Architecture

**pysvsim.py** - Main simulator with these core classes:

- **SystemVerilogParser**: Regex-based parser extracting modules, ports, buses, wires, assignments, and `always_ff` blocks
- **LogicEvaluator**: Evaluates combinational logic expressions; handles hierarchical module instantiation and NAND gate counting
- **SequentialLogicEvaluator**: Extends LogicEvaluator for sequential logic with state across clock cycles
- **TruthTableGenerator/ImageGenerator**: Generates truth tables and PNG visualizations
- **WaveformImageGenerator**: Creates timing diagrams for sequential logic
- **TestRunner**: Executes JSON test cases against modules

**test_runner.py** - Parallel test framework using `ProcessPoolExecutor` for multi-core execution

## Module System

- Modules resolve from the same directory as the parent module
- `GLOBAL_MODULE_CACHE` prevents re-parsing; use `clear_module_cache()` for test isolation
- NAND gate counting recurses through module instantiation hierarchy

## ROM Primitives

Modules with a `rom_` prefix are treated as built-in ROM primitives by the simulator. The SV file only needs to declare the interface — the simulator handles data loading automatically.

**Naming convention**: `rom_{name}` loads `{name}.txt`
- `rom_deadbeef` loads `deadbeef.txt`
- `rom_instruction_memory` loads `instruction_memory.txt`

**Data file search order**:
1. Same directory as the SV file
2. `roms/` subdirectory relative to SV file
3. `roms/` relative to CWD

**Example SV file** (`parts/rom_deadbeef.sv`):
```systemverilog
module rom_deadbeef (
    input  logic [1:0] addr,
    output logic [7:0] data
);
    // ROM data loaded from deadbeef.txt by simulator
endmodule
```

**Data file format** (`parts/deadbeef.txt`): one binary value per line, one entry per address:
```
11011110
10101101
10111110
11101111
```

The address width determines ROM depth (2-bit addr = 4 entries). The output bus width determines word size. Data files use the same format as memory init files (binary strings, `#`/`//` comments, optional `addr:value` syntax).

## Test File Conventions

Test files share the same base name as their SystemVerilog file:
- `parts/and_gate.sv` + `parts/and_gate.json`

**Combinational format:**
```json
[{"inA": 0, "inB": 0, "expect": {"outY": 1}}]
```

**Sequential format:**
```json
{
    "sequential": true,
    "test_cases": [{"name": "test", "sequence": [{"inputs": {...}, "expected": {...}}]}]
}
```

## SystemVerilog Support

**Combinational**: Module declarations, buses (`[7:0]`), bit selection (`A[2]`), concatenation (`{a,b}`), bitwise operators (`&|^~`), literals (`8'hFF`), arithmetic in assign (`+`, `-`, `*`), ternary operator (`sel ? a : b`), `always_comb` blocks with if/else and case statements

**Sequential**: `always_ff @(posedge clk)`, if/else chains, arithmetic (`count + 1`), clock/enable/reset

**ROM Primitives**: Modules named `rom_*` are auto-detected as ROM primitives. The simulator strips the `rom_` prefix to find the data file (e.g., `rom_deadbeef` loads `deadbeef.txt`). No assignments or logic needed in the SV file — just declare ports.

**Limitations**: Modules must be in same directory; no timing simulation

## Key Directories

- **parts/**: Verified module library (gates, adders, muxes, registers, counters, ROMs)
- **testing/**: HDLBits coursework modules for testing
- **goals/**: Project milestone documents (8-bit CPU, RV32I plans)
- **roms/**: ROM data files (blank templates and CPU data)
