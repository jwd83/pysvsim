# pysvsim Test Report

**Generated:** 2025-10-13 06:20:52

## Summary

- **Total Test Cases:** 10
- **Passed:** 10 ✅
- **Failed:** 0 ❌
- **Success Rate:** 100.0%

## Test Results

### 1. NAND Gate ✅

**File:** `nand_gate.sv`
**Description:** Basic NAND gate implementation with assign statement
**Execution Time:** 0.043s

**Inputs Parsed:** ['inA', 'inB'] ✅
**Outputs Parsed:** ['outY'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 4/4 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: nand_gate.sv
Module: nand_gate
Inputs: ['inA', 'inB']
Outputs: ['outY']
Truth Table:
inA inB | outY
--------------
  0   0 |   1
  0   1 |   1
  1   0 |   1
  1   1 |   0

Running tests...
Test 1 passed
Test 2 passed
Test 3 passed
Test 4 passed

Test Results: 4/4 passed
All tests passed!

```

---

### 2. Inverter ✅

**File:** `inverter.sv`
**Description:** Inverter built using NAND gate module instantiation
**Execution Time:** 0.050s

**Inputs Parsed:** ['in'] ✅
**Outputs Parsed:** ['out'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 2/2 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: inverter.sv
Module: inverter
Inputs: ['in']
Outputs: ['out']
Truth Table:
 in | out
---------
  0 |   1
  1 |   0

Running tests...
Test 1 passed
Test 2 passed

Test Results: 2/2 passed
All tests passed!

```

---

### 3. AND Gate ✅

**File:** `and_gate.sv`
**Description:** AND gate built from hierarchical NAND + inverter modules
**Execution Time:** 0.050s

**Inputs Parsed:** ['inA', 'inB'] ✅
**Outputs Parsed:** ['outY'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 4/4 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: and_gate.sv
Module: and_gate
Inputs: ['inA', 'inB']
Outputs: ['outY']
Truth Table:
inA inB | outY
--------------
  0   0 |   0
  0   1 |   0
  1   0 |   0
  1   1 |   1

Running tests...
Test 1 passed
Test 2 passed
Test 3 passed
Test 4 passed

Test Results: 4/4 passed
All tests passed!

```

---

### 4. OR Gate ✅

**File:** `or_gate.sv`
**Description:** OR gate built using De Morgan's law with inverters + NAND
**Execution Time:** 0.050s

**Inputs Parsed:** ['inA', 'inB'] ✅
**Outputs Parsed:** ['outY'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 4/4 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: or_gate.sv
Module: or_gate
Inputs: ['inA', 'inB']
Outputs: ['outY']
Truth Table:
inA inB | outY
--------------
  0   0 |   0
  0   1 |   1
  1   0 |   1
  1   1 |   1

Running tests...
Test 1 passed
Test 2 passed
Test 3 passed
Test 4 passed

Test Results: 4/4 passed
All tests passed!

```

---

### 5. XOR Gate ✅

**File:** `xor_gate.sv`
**Description:** XOR gate built using (A & ~B) | (~A & B) with AND/OR/inverter modules
**Execution Time:** 0.060s

**Inputs Parsed:** ['inA', 'inB'] ✅
**Outputs Parsed:** ['outY'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 4/4 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: xor_gate.sv
Module: xor_gate
Inputs: ['inA', 'inB']
Outputs: ['outY']
Truth Table:
inA inB | outY
--------------
  0   0 |   0
  0   1 |   1
  1   0 |   1
  1   1 |   0

Running tests...
Test 1 passed
Test 2 passed
Test 3 passed
Test 4 passed

Test Results: 4/4 passed
All tests passed!

```

---

### 6. NOR Gate ✅

**File:** `nor_gate.sv`
**Description:** NOR gate built using OR gate + inverter (NOT OR)
**Execution Time:** 0.050s

**Inputs Parsed:** ['inA', 'inB'] ✅
**Outputs Parsed:** ['outY'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 4/4 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: nor_gate.sv
Module: nor_gate
Inputs: ['inA', 'inB']
Outputs: ['outY']
Truth Table:
inA inB | outY
--------------
  0   0 |   1
  0   1 |   0
  1   0 |   0
  1   1 |   0

Running tests...
Test 1 passed
Test 2 passed
Test 3 passed
Test 4 passed

Test Results: 4/4 passed
All tests passed!

```

---

### 7. Half Adder ✅

**File:** `half_adder.sv`
**Description:** Half adder built from XOR and AND gate modules (hierarchical design)
**Execution Time:** 0.060s

**Inputs Parsed:** ['A', 'B'] ✅
**Outputs Parsed:** ['Sum', 'Carry'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 4/4 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: half_adder.sv
Module: half_adder
Inputs: ['A', 'B']
Outputs: ['Sum', 'Carry']
Truth Table:
  A   B | Sum Carry
-------------------
  0   0 |   0   0
  0   1 |   1   0
  1   0 |   1   0
  1   1 |   0   1

Running tests...
Test 1 passed
Test 2 passed
Test 3 passed
Test 4 passed

Test Results: 4/4 passed
All tests passed!

```

---

### 8. Full Adder ✅

**File:** `full_adder.sv`
**Description:** Full adder built from two half adders with carry chain
**Execution Time:** 0.100s

**Inputs Parsed:** ['A', 'B', 'Cin'] ✅
**Outputs Parsed:** ['Sum', 'Cout'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 8/8 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: full_adder.sv
Module: full_adder
Inputs: ['A', 'B', 'Cin']
Outputs: ['Sum', 'Cout']
Truth Table:
  A   B Cin | Sum Cout
----------------------
  0   0   0 |   0   0
  0   0   1 |   1   0
  0   1   0 |   1   0
  0   1   1 |   0   1
  1   0   0 |   1   0
  1   0   1 |   0   1
  1   1   0 |   0   1
  1   1   1 |   1   1

Running tests...
Test 1 passed
Test 2 passed
Test 3 passed
Test 4 passed
Test 5 passed
Test 6 passed
Test 7 passed
Test 8 passed

Test Results: 8/8 passed
All tests passed!

```

---

### 9. 1-bit ALU ✅

**File:** `alu_1bit.sv`
**Description:** Hierarchical 1-bit ALU with 4 operations (AND, OR, XOR, ADD) built from gate modules
**Execution Time:** 0.464s

**Inputs Parsed:** ['A', 'B', 'Cin', 'Op0', 'Op1'] ✅
**Outputs Parsed:** ['Result', 'Cout'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 17/17 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: alu_1bit.sv
Module: alu_1bit
Inputs: ['A', 'B', 'Cin', 'Op0', 'Op1']
Outputs: ['Result', 'Cout']
Truth Table:
  A   B Cin Op0 Op1 | Result Cout
---------------------------------
  0   0   0   0   0 |   0   0
  0   0   0   0   1 |   0   0
  0   0   0   1   0 |   0   0
  0   0   0   1   1 |   0   0
  0   0   1   0   0 |   0   0
  0   0   1   0   1 |   0   0
  0   0   1   1   0 |   0   0
  0   0   1   1   1 |   1   0
  0   1   0   0   0 |   0   0
  0   1   0   0   1 |   1   0
  0   1   0   1   0 |   1   0
  0   1   0   1   1 |   1   0
  0   1   1   0   0 |   0   0
  0   1   1   0   1 |   1   0
  0   1   1   1   0 |   1   0
  0   1   1   1   1 |   0   1
  1   0   0   0   0 |   0   0
  1   0   0   0   1 |   1   0
  1   0   0   1   0 |   1   0
  1   0   0   1   1 |   1   0
  1   0   1   0   0 |   0   0
  1   0   1   0   1 |   1   0
  1   0   1   1   0 |   1   0
  1   0   1   1   1 |   0   1
  1   1   0   0   0 |   1   0
  1   1   0   0   1 |   0   0
  1   1   0   1   0 |   1   0
  1   1   0   1   1 |   0   1
  1   1   1   0   0 |   1   0
  1   1   1   0   1 |   0   0
  1   1   1   1   0 |   1   0
  1   1   1   1   1 |   1   1

Running tests...
Test 1 passed
Test 2 passed
Test 3 passed
Test 4 passed
Test 5 passed
Test 6 passed
Test 7 passed
Test 8 passed
Test 9 passed
Test 10 passed
Test 11 passed
Test 12 passed
Test 13 passed
Test 14 passed
Test 15 passed
Test 16 passed
Test 17 passed

Test Results: 17/17 passed
All tests passed!

```

---

### 10. Complex Logic ✅

**File:** `complex_logic.sv`
**Description:** Multi-output module with various bitwise operations
**Execution Time:** 0.048s

**Inputs Parsed:** ['a', 'b', 'c'] ✅
**Outputs Parsed:** ['out1', 'out2', 'out3'] ✅
**Truth Table:** Generated ✅
**Test Cases:** No test file specified (truth table only)

**Complete Output:**
```
Parsing SystemVerilog file: complex_logic.sv
Module: complex_logic
Inputs: ['a', 'b', 'c']
Outputs: ['out1', 'out2', 'out3']
Truth Table:
  a   b   c | out1 out2 out3
----------------------------
  0   0   0 |   0   0   0
  0   0   1 |   0   1   0
  0   1   0 |   0   0   0
  0   1   1 |   0   1   1
  1   0   0 |   0   1   1
  1   0   1 |   0   1   1
  1   1   0 |   1   1   1
  1   1   1 |   1   1   0

```

---

## System Information

- **Python:** 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]
- **Platform:** win32
- **Working Directory:** C:\Users\jared\pysvsim
- **pysvsim Script:** pysvsim.py