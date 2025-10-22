# 8-Bit CPU Milestone

## Goal
Design and test a simple 8-bit CPU capable of executing basic instructions from ROM.

---

## Current Status: Existing Modules

### Arithmetic & Logic
- ✅ Full/Half Adders (1-bit)
- ✅ Adders (4-bit, 8-bit, 16-bit, 32-bit, 64-bit)
- ✅ Carry-Select Adders (8-bit, 16-bit, 32-bit, 64-bit)
- ✅ Basic logic gates (AND, OR, NOT, NAND, NOR, XOR, XNOR)
- ✅ 8-bit logic gates (AND, OR, NOT, NAND, NOR, XOR, XNOR)

### Data Path Components
- ✅ Multiplexers: 2:1 (1-bit, 4-bit, 8-bit, 16-bit, 32-bit)
- ✅ Registers (1-bit, 8-bit, 16-bit, 32-bit, 64-bit)
- ✅ 8-bit counter

### ROM Support
- ✅ ROM loading system defined (roms folder with .txt format)

---

## Required New Modules for 8-Bit CPU

### 1. **ROM Module** (Critical)
- **File:** `parts/rom_program.sv`
- **Description:** Instruction ROM module that interfaces with the simulator's ROM loading system
- **Ports:**
  - `input [7:0] address` - 8-bit address input (256 byte address space)
  - `output [7:0] data` - 8-bit data output (instruction fetch)
- **Notes:** Must integrate with existing ROM .txt file loading from `roms/` folder

### 2. **Program Counter (PC)** (Critical)
- **File:** `parts/program_counter_8bit.sv`
- **Description:** 8-bit counter with load capability for jumps
- **Ports:**
  - `input clk, reset, load, enable`
  - `input [7:0] load_value` - Jump target address
  - `output [7:0] pc` - Current program counter value
- **Notes:** Extends the existing counter8 with load/jump functionality

### 3. **Instruction Decoder** (Critical)
- **File:** `parts/instruction_decoder_8bit.sv`
- **Description:** Decodes 8-bit instructions into control signals
- **Suggested Simple Instruction Format:**
  - `[7:6]` - Opcode (2 bits = 4 instructions)
  - `[5:3]` - Source/Dest register (3 bits = 8 registers)
  - `[2:0]` - Operand/Address (3 bits)
- **Example Opcodes:**
  - `00` - LOAD (load from immediate/memory)
  - `01` - ADD (add to accumulator)
  - `10` - STORE (store to memory)
  - `11` - JUMP (conditional/unconditional jump)
- **Outputs:** All control signals needed by datapath
  - ALU operation select
  - Register write enable
  - Memory write enable
  - PC load enable
  - Data source mux selects

### 4. **Register File** (Critical)
- **File:** `parts/register_file_8x8bit.sv`
- **Description:** 8 registers of 8 bits each with dual read, single write
- **Ports:**
  - `input clk, write_enable`
  - `input [2:0] read_addr_a, read_addr_b, write_addr`
  - `input [7:0] write_data`
  - `output [7:0] read_data_a, read_data_b`
- **Notes:** Can be built from eight 8-bit registers with mux logic

### 5. **ALU (Arithmetic Logic Unit)** (Critical)
- **File:** `parts/alu_8bit.sv`
- **Description:** 8-bit ALU supporting basic operations
- **Ports:**
  - `input [7:0] a, b` - Operands
  - `input [2:0] operation` - Operation select
  - `output [7:0] result`
  - `output zero, carry, negative` - Status flags
- **Suggested Operations:**
  - `000` - ADD
  - `001` - SUB (using 2's complement)
  - `010` - AND
  - `011` - OR
  - `100` - XOR
  - `101` - NOT A
  - `110` - PASS A
  - `111` - PASS B

### 6. **RAM Module** (Important)
- **File:** `parts/ram_256x8bit.sv`
- **Description:** 256 bytes of RAM for data storage
- **Ports:**
  - `input clk, write_enable`
  - `input [7:0] address`
  - `input [7:0] write_data`
  - `output [7:0] read_data`
- **Notes:** Sequential logic; may require simulator enhancement for memory arrays

### 7. **Status Register (Flags)** (Important)
- **File:** `parts/status_register.sv`
- **Description:** Stores ALU flags (Zero, Carry, Negative, etc.)
- **Ports:**
  - `input clk, reset, update_enable`
  - `input zero, carry, negative` - Flag inputs from ALU
  - `output [2:0] flags` - Current flag values
- **Notes:** Used for conditional branching

### 8. **Comparator** (Helpful)
- **File:** `parts/comparator_8bit.sv`
- **Description:** 8-bit equality and magnitude comparator
- **Ports:**
  - `input [7:0] a, b`
  - `output equal, greater, less`
- **Notes:** Can be built from XOR gates and comparison logic; useful for branches

### 9. **4:1 Multiplexer (8-bit)** (Helpful)
- **File:** `parts/mux_4to1_8bit.sv`
- **Description:** 4-input multiplexer for data path routing
- **Ports:**
  - `input [7:0] in0, in1, in2, in3`
  - `input [1:0] select`
  - `output [7:0] out`
- **Notes:** Can be built from three 2:1 muxes

### 10. **Subtractor** (Optional)
- **File:** `parts/subtractor_8bit.sv`
- **Description:** 8-bit subtractor using 2's complement
- **Ports:**
  - `input [7:0] a, b`
  - `output [7:0] difference`
  - `output borrow`
- **Notes:** Can integrate into ALU instead

---

## Simulator Enhancements Needed

### 1. **ROM Loading Support** (Critical)
- Extend simulator to load ROM data from `roms/*.txt` files
- Map ROM module instances (e.g., `rom_program`) to corresponding `.txt` files
- Parse ROM file format and populate memory during initialization

### 2. **RAM/Memory Array Support** (Important)
- Add support for `reg [7:0] memory [255:0];` style memory arrays
- Implement read/write semantics for memory arrays in sequential logic
- Handle memory indexing with variable addresses

### 3. **Extended Sequential Testing** (Helpful)
- Support longer test sequences for CPU execution traces
- Allow cycle-by-cycle verification of multi-instruction programs
- Enhanced waveform output for debugging CPU state

---

## Development Phases

### Phase 1: Core Datapath (Week 1)
1. Program Counter with load
2. Register File (8x8-bit)
3. ALU (8-bit with 8 operations)
4. Status Register

### Phase 2: Control & Memory (Week 2)
1. Instruction Decoder
2. ROM module + simulator ROM loading
3. RAM module + simulator RAM support
4. 4:1 Multiplexer (8-bit)

### Phase 3: Integration & Testing (Week 3)
1. Top-level CPU module integrating all components
2. Simple instruction set definition document
3. Test programs in ROM format
4. Full CPU simulation and validation

### Phase 4: Verification (Week 4)
1. Comprehensive test suite for each module
2. Multi-instruction test programs (fibonacci, sum, etc.)
3. CPU waveform visualization
4. NAND gate count analysis

---

## Estimated Complexity

- **Module Count:** ~10 new modules
- **Total NAND Gates (estimate):** ~5,000-10,000 gates
- **Test Cases:** ~100-150 new test cases
- **Simulator LOC:** ~500-800 lines of new code

---

## Success Criteria

1. ✅ All individual modules pass unit tests
2. ✅ CPU can fetch instructions from ROM
3. ✅ CPU can execute a simple 5-10 instruction program
4. ✅ CPU correctly updates PC, registers, and flags
5. ✅ Waveform visualization shows correct execution trace
6. ✅ NAND gate count is calculated and reasonable

---

## Example First Program (ROM)

```
Address | Instruction | Assembly | Description
--------|-------------|----------|-------------
0x00    | 00000001    | LOAD R0, #1 | Load immediate 1 into R0
0x01    | 01000000    | ADD R0, R0  | Add R0 to itself (R0 = 2)
0x02    | 01000000    | ADD R0, R0  | Add R0 to itself (R0 = 4)
0x03    | 10000000    | STORE R0, 0 | Store R0 to memory[0]
0x04    | 11000100    | JUMP 0x04   | Infinite loop (halt)
```

This program loads 1, doubles it twice to get 4, stores the result, and halts.

---

## Notes

- Start with the **simplest possible instruction set** (4-8 instructions)
- Use **fixed-length 8-bit instructions** for simplicity
- Focus on **load, store, add, and jump** as core operations
- Registers can be implicit (accumulator-based) or explicit (register file)
- Consider a **Harvard architecture** (separate instruction/data memory) for simplicity

---

## Next Steps

1. Review and refine this milestone document
2. Prioritize critical modules (PC, ROM, Instruction Decoder, ALU, Register File)
3. Design instruction set architecture (ISA) document
4. Begin Phase 1 development with Program Counter
