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

**Combinational**: Module declarations, buses (`[7:0]`), bit selection (`A[2]`), concatenation (`{a,b}`), bitwise operators (`&|^~`), literals (`8'hFF`)

**Sequential**: `always_ff @(posedge clk)`, if/else chains, arithmetic (`count + 1`), clock/enable/reset

**Limitations**: Arithmetic only in sequential blocks (combinational uses adder modules); modules must be in same directory; no timing simulation; no memory arrays yet

## Key Directories

- **parts/**: Verified module library (gates, adders, muxes, registers, counters)
- **testing/**: HDLBits coursework modules for testing
- **goals/**: Project milestone documents (8-bit CPU, RV32I plans)
- **roms/**: ROM data files for future CPU implementation
