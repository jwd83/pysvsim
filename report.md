# pysvsim Test Report

**Generated:** 2025-10-13 05:06:39

## Summary

- **Total Test Cases:** 4
- **Passed:** 4 ✅
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

**Sample Output:**
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
... (truncated)
```

---

### 2. Inverter ✅

**File:** `inverter.sv`
**Description:** Inverter built using NAND gate module instantiation
**Execution Time:** 0.044s

**Inputs Parsed:** ['in'] ✅
**Outputs Parsed:** ['out'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 2/2 passed ✅

**Sample Output:**
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

... (truncated)
```

---

### 3. AND Gate ✅

**File:** `and_gate.sv`
**Description:** AND gate built from hierarchical NAND + inverter modules
**Execution Time:** 0.046s

**Inputs Parsed:** ['inA', 'inB'] ✅
**Outputs Parsed:** ['outY'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 4/4 passed ✅

**Sample Output:**
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
... (truncated)
```

---

### 4. Complex Logic ✅

**File:** `complex_logic.sv`
**Description:** Multi-output module with various bitwise operations
**Execution Time:** 0.046s

**Inputs Parsed:** ['a', 'b', 'c'] ✅
**Outputs Parsed:** ['out1', 'out2', 'out3'] ✅
**Truth Table:** Generated ✅
**Test Cases:** No test file specified (truth table only)

**Sample Output:**
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
... (truncated)
```

---

## System Information

- **Python:** 3.13.2 (main, Feb 12 2025, 14:49:53) [MSC v.1942 64 bit (AMD64)]
- **Platform:** win32
- **Working Directory:** C:\Users\jared\pysvsim
- **pysvsim Script:** pysvsim.py