# PySVSim Project Summary

## What Is This?

PySVSim is a pure Python SystemVerilog simulator designed for an educational digital logic game. Players write hardware modules in SystemVerilog, starting from basic NAND gates and building up to complete CPUs.

## Current Capabilities

### Simulation Engine
- **Combinational logic**: Bitwise operators, buses, concatenation, replication
- **Sequential logic**: `always_ff` blocks with clock, enable, reset
- **Hierarchical design**: Module instantiation with automatic dependency loading
- **NAND gate analysis**: Counts gates recursively through the design hierarchy

### Testing & Visualization
- **Truth tables**: Automatic generation for combinational modules
- **Waveforms**: Professional timing diagrams for sequential modules
- **PNG output**: Game-ready images for truth tables and waveforms
- **Parallel testing**: Multi-core test execution for faster regression

### Module Library (36+ modules)
- **Logic gates**: NAND, AND, OR, NOR, XOR, XNOR, NOT (1-bit and 8-bit)
- **Adders**: Half, Full, Ripple-carry (4-64 bit), Carry-select (8-64 bit)
- **Multiplexers**: 2:1 (1/4/8/16/32-bit)
- **Registers**: 1/8/16/32/64-bit with clock/enable
- **Counter**: 8-bit with reset/enable

## Key Files

| File | Purpose |
|------|---------|
| `pysvsim.py` | Main simulator (parser, evaluators, generators) |
| `test_runner.py` | Parallel test execution framework |
| `parts/` | Verified module library with tests |
| `testing/` | HDLBits coursework modules |
| `goals/` | Project milestones and planning |

## Performance Characteristics

- **Truth tables**: 16 combinations default (configurable)
- **Parallel testing**: ~39% speedup on multi-core systems
- **Simulation speed**: Ripple-carry adders 5.6× faster than carry-select
- **Module caching**: Parsed modules cached globally for reuse

## Next Development Steps

### Immediate: 8-bit CPU
1. **ROM module**: Load programs from `roms/*.txt` files
2. **Program counter**: 8-bit with increment and jump
3. **Instruction decoder**: Simple 4-8 instruction ISA
4. **Register file**: 8 registers × 8 bits
5. **ALU integration**: Connect existing adder modules
6. **RAM module**: 256 × 8-bit data memory

### Simulator Enhancements Needed
- Memory array support (`reg [7:0] mem [255:0]`)
- ROM file loading integration
- Extended sequential test support for CPU traces

### Future Milestones
- Overture/LEG ISAs (from Turing Complete game)
- RV32I RISC-V CPU with serial I/O
- FPGA port to Tang Nano 20K
- Game console implementation

## Running the Project

```bash
# Test single module
python test_runner.py parts/and_gate.sv

# Test all modules
python test_runner.py parts/

# Run batch tests
test.bat
```

## Documentation

- **README.md**: User guide and feature overview
- **AGENTS.md**: Instructions for AI assistants
- **goals/plan.md**: Development roadmap
- **goals/8bitcpu-milestone.md**: 8-bit CPU detailed plan
- **goals/rv32i-milestone.md**: RISC-V implementation plan

## Technical Notes

- Python 3.13+ required
- matplotlib for PNG generation
- Regex-based parsing (no external parser dependencies)
- All modules built hierarchically from NAND gates
- Test coverage: 250+ test cases across all modules
