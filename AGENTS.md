# AI Agent Instructions for PySVSim

This document provides context and guidelines for AI agents working on this SystemVerilog simulator codebase.

## Project Overview

PySVSim is a pure Python SystemVerilog simulator designed for integration into an educational digital logic game. It supports both combinational and sequential logic simulation with a focus on hierarchical module design built from NAND gates.

## Key Files

- **pysvsim.py**: Main simulator with parser, evaluators, and truth table generator
- **test_runner.py**: Parallel test execution framework with detailed reporting
- **parts/**: Library of verified SystemVerilog modules (gates, adders, registers)
- **testing/**: Additional test modules from HDLBits coursework
- **goals/**: Project milestones and planning documents

## Architecture

### Core Classes (in pysvsim.py)

1. **SystemVerilogParser**: Parses .sv files into module info dictionaries
   - Handles ports, wires, assignments, instantiations, sequential blocks
   - Supports buses, bit selection, concatenation, replication

2. **LogicEvaluator**: Evaluates combinational logic
   - Bus expansion/collection
   - Expression evaluation with operators
   - Hierarchical module instantiation
   - NAND gate counting

3. **SequentialLogicEvaluator**: Extends LogicEvaluator for sequential logic
   - State management across clock cycles
   - Conditional assignment evaluation
   - Arithmetic expression support

4. **TruthTableGenerator**: Creates truth tables for combinational modules
5. **TestRunner**: Executes JSON test cases

### Global State

- **GLOBAL_MODULE_CACHE**: Caches parsed modules to avoid re-parsing
- Use `clear_module_cache()` when testing module changes

## Testing

### Running Tests

```bash
# Single file
python test_runner.py parts/and_gate.sv

# Directory (parallel)
python test_runner.py parts/

# Batch
test.bat
```

### Test File Conventions

- JSON test files share the same base name as .sv files
- Alternative names: `module.json`, `module_test.json`, `module_tests.json`

### Test Output

- Combinational: Truth table + PNG image
- Sequential: Test results + waveform PNG

## Design Principles

### Module Hierarchy

All modules are built hierarchically from `nand_gate.sv` as the primitive:
```
nand_gate → not_gate → and_gate → half_adder → full_adder → adder_4bit → ...
```

### Naming Conventions

- Inputs: `inA`, `inB`, `inCarry`, `clk`, `reset`, `enable`, `data`
- Outputs: `outY`, `outSum`, `outCarry`, `count`
- Buses: `[7:0] data`, `[3:0] A`
- Instances: `u_fa0`, `u_lower`, `u_upper`

### NAND Gate Counting

The simulator counts NAND gates recursively through module instantiations. This is used for complexity analysis in the educational game context.

## Common Tasks

### Adding a New Module

1. Create `parts/module_name.sv` using existing modules
2. Create `parts/module_name.json` with test cases
3. Run `python test_runner.py parts/module_name.sv` to verify
4. Check NAND gate count in output

### Fixing Parser Issues

Common issues and locations:
- Port parsing: `_parse_port_list()`, `_parse_port_section()`
- Bus slices: `_parse_assignments()`, `_evaluate_expression()`
- Concatenation: `_evaluate_concatenation()`
- Instantiation: `_parse_instantiations()`, `_evaluate_instantiation()`

### Adding New Features

1. Add parsing in `SystemVerilogParser`
2. Add evaluation in `LogicEvaluator` or `SequentialLogicEvaluator`
3. Add tests in `parts/` or `testing/`
4. Update README.md if user-facing

## Known Limitations

- Arithmetic operators only work in sequential blocks
- Modules must be in same directory as parent module
- No memory array support (reg [7:0] mem [255:0])
- No timing/propagation delay simulation

## Current Development Focus

See `goals/` for detailed milestones:
- **8bitcpu-milestone.md**: Simple 8-bit CPU with ROM/RAM
- **rv32i-milestone.md**: Full RISC-V 32-bit implementation
- **plan.md**: High-level project direction

## Debugging Tips

1. **Parser issues**: Print `module_info` dict after parsing
2. **Evaluation issues**: Add debug prints in `_evaluate_expression()`
3. **Instantiation issues**: Check `_evaluate_instantiation()` signal mapping
4. **Test failures**: Compare actual vs expected in test output

## Code Style

- Pure Python 3.13+
- Regex-based parsing (no external parser libraries)
- Type hints where practical
- Docstrings for public methods
- Comments for complex logic

## Performance Notes

- Ripple-carry adders simulate ~5.6× faster than carry-select
- Use ripple-carry during development, carry-select for hardware
- Global module cache significantly speeds up repeated evaluations
- Test runner uses ProcessPoolExecutor for parallel file testing
