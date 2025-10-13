# pysvsim Test Report

**Generated:** 2025-10-13 05:39:43

## Summary

- **Total Test Cases:** 8
- **Passed:** 8 ✅
- **Failed:** 0 ❌
- **Success Rate:** 100.0%

## Test Results

### 1. NAND Gate ✅

**File:** `nand_gate.sv`
**Description:** Basic NAND gate implementation with assign statement
**Execution Time:** 0.046s

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
**Execution Time:** 0.045s

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
**Execution Time:** 0.047s

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
**Execution Time:** 0.047s

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

### 5. Half Adder ✅

**File:** `half_adder.sv`
**Description:** Half adder with XOR sum and AND carry logic
**Execution Time:** 0.046s

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

### 6. Full Adder ✅

**File:** `full_adder.sv`
**Description:** Full adder built from two half adders with carry chain
**Execution Time:** 0.046s

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

### 7. 1-bit ALU ✅

**File:** `alu_1bit.sv`
**Description:** 1-bit ALU slice with 8 operations (AND, OR, XOR, ADD, SUB, NOT, PASS)
**Execution Time:** 0.059s

**Inputs Parsed:** ['A', 'B', 'Cin', 'Op0', 'Op1', 'Op2'] ✅
**Outputs Parsed:** ['Result', 'Cout'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 33/33 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: alu_1bit.sv
Module: alu_1bit
Inputs: ['A', 'B', 'Cin', 'Op0', 'Op1', 'Op2']
Outputs: ['Result', 'Cout']
Truth Table:
  A   B Cin Op0 Op1 Op2 | Result Cout
-------------------------------------
  0   0   0   0   0   0 |   0   0
  0   0   0   0   0   1 |   1   0
  0   0   0   0   1   0 |   0   0
  0   0   0   0   1   1 |   0   0
  0   0   0   1   0   0 |   0   0
  0   0   0   1   0   1 |   1   0
  0   0   0   1   1   0 |   0   0
  0   0   0   1   1   1 |   0   0
  0   0   1   0   0   0 |   0   0
  0   0   1   0   0   1 |   0   1
  0   0   1   0   1   0 |   0   0
  0   0   1   0   1   1 |   0   0
  0   0   1   1   0   0 |   0   0
  0   0   1   1   0   1 |   1   0
  0   0   1   1   1   0 |   1   0
  0   0   1   1   1   1 |   0   0
  0   1   0   0   0   0 |   0   0
  0   1   0   0   0   1 |   0   0
  0   1   0   0   1   0 |   1   0
  0   1   0   0   1   1 |   0   0
  0   1   0   1   0   0 |   1   0
  0   1   0   1   0   1 |   1   0
  0   1   0   1   1   0 |   1   0
  0   1   0   1   1   1 |   1   0
  0   1   1   0   0   0 |   0   0
  0   1   1   0   0   1 |   1   0
  0   1   1   0   1   0 |   1   0
  0   1   1   0   1   1 |   0   0
  0   1   1   1   0   0 |   1   0
  0   1   1   1   0   1 |   1   0
  0   1   1   1   1   0 |   0   1
  0   1   1   1   1   1 |   1   0
  1   0   0   0   0   0 |   0   0
  1   0   0   0   0   1 |   0   1
  1   0   0   0   1   0 |   1   0
  1   0   0   0   1   1 |   1   0
  1   0   0   1   0   0 |   1   0
  1   0   0   1   0   1 |   0   0
  1   0   0   1   1   0 |   1   0
  1   0   0   1   1   1 |   0   0
  1   0   1   0   0   0 |   0   0
  1   0   1   0   0   1 |   1   1
  1   0   1   0   1   0 |   1   0
  1   0   1   0   1   1 |   1   0
  1   0   1   1   0   0 |   1   0
  1   0   1   1   0   1 |   0   0
  1   0   1   1   1   0 |   0   1
  1   0   1   1   1   1 |   0   0
  1   1   0   0   0   0 |   1   0
  1   1   0   0   0   1 |   1   0
  1   1   0   0   1   0 |   0   0
  1   1   0   0   1   1 |   1   0
  1   1   0   1   0   0 |   1   0
  1   1   0   1   0   1 |   0   0
  1   1   0   1   1   0 |   0   1
  1   1   0   1   1   1 |   1   0
  1   1   1   0   0   0 |   1   0
  1   1   1   0   0   1 |   0   1
  1   1   1   0   1   0 |   0   0
  1   1   1   0   1   1 |   1   0
  1   1   1   1   0   0 |   1   0
  1   1   1   1   0   1 |   0   0
  1   1   1   1   1   0 |   1   1
  1   1   1   1   1   1 |   1   0

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
Test 18 passed
Test 19 passed
Test 20 passed
Test 21 passed
Test 22 passed
Test 23 passed
Test 24 passed
Test 25 passed
Test 26 passed
Test 27 passed
Test 28 passed
Test 29 passed
Test 30 passed
Test 31 passed
Test 32 passed
Test 33 passed

Test Results: 33/33 passed
All tests passed!

```

---

### 8. Complex Logic ✅

**File:** `complex_logic.sv`
**Description:** Multi-output module with various bitwise operations
**Execution Time:** 0.045s

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

- **Python:** 3.13.2 (main, Feb 12 2025, 14:49:53) [MSC v.1942 64 bit (AMD64)]
- **Platform:** win32
- **Working Directory:** C:\Users\jared\pysvsim
- **pysvsim Script:** pysvsim.py