# PySVSim Project Summary

## What This Is

PySVSim is a pure Python SystemVerilog simulator for an educational digital logic game. It parses modules, evaluates logic, generates truth tables/waveforms, and runs JSON-based tests.

## Verified Current State (February 8, 2026)

- `parts/` regression: 36/36 files passing, 316/316 test cases
- `testing/` regression: 40/40 files passing, 261/261 test cases
- Combined: 76 files passing, 577/577 test cases
- Total NAND gates across `parts/`: 13,092

## Current Capabilities

### Simulation Engine
- Combinational logic with buses, bit selection, concatenation, replication, and bitwise operators
- Sequential logic via `always_ff @(posedge clk)` with stateful cycle evaluation
- Hierarchical module instantiation with module caching
- Recursive NAND gate counting across instantiated submodules

### Testing and Visualization
- Truth table generation for combinational modules
- Waveform PNG generation for sequential test sequences
- JSON test support for both combinational and sequential formats
- Parallel test execution via `ProcessPoolExecutor`

### Module Library (`parts/`)
- Logic gates: NAND, AND, OR, NOR, XOR, XNOR, NOT (1-bit and 8-bit)
- Adders: half/full, ripple-carry (4/8/16/32/64-bit), carry-select (8/16/32/64-bit)
- Multiplexers: 2:1 (1/4/8/16/32-bit)
- Registers: 1/8/16/32/64-bit
- Counter: 8-bit with reset/enable

## Known Limits

- Arithmetic operators are supported in sequential blocks; combinational arithmetic should use module composition (e.g. adder modules)
- Modules are resolved from the same directory as the parent module
- No timing delay simulation
- Memory arrays are supported (`reg/logic [W] mem [D]`) with ROM/RAM initialization via test JSON bindings

## Common Commands

```bash
# Run simulator on one module
uv run pysvsim.py --file parts/full_adder.sv --test parts/full_adder.json

# Run regressions
uv run test_runner.py parts/
uv run test_runner.py testing/
```
