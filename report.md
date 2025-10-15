# pysvsim Test Report

**Generated:** 2025-10-15 05:06:18

## Summary

- **Total Test Cases:** 11
- **Passed:** 11 ✅
- **Failed:** 0 ❌
- **Success Rate:** 100.0%

## Test Results

### 1. NAND Gate ✅

**File:** `nand_gate.sv`
**Description:** Basic NAND gate implementation with assign statement
**Execution Time:** 0.049s

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
   inA    inB |   outY
----------------------
     0      0 |      1
     0      1 |      1
     1      0 |      1
     1      1 |      0

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
**Execution Time:** 0.055s

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
    in |    out
---------------
     0 |      1
     1 |      0

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
   inA    inB |   outY
----------------------
     0      0 |      0
     0      1 |      0
     1      0 |      0
     1      1 |      1

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
**Execution Time:** 0.058s

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
   inA    inB |   outY
----------------------
     0      0 |      0
     0      1 |      1
     1      0 |      1
     1      1 |      1

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
**Execution Time:** 0.068s

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
   inA    inB |   outY
----------------------
     0      0 |      0
     0      1 |      1
     1      0 |      1
     1      1 |      0

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
**Execution Time:** 0.061s

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
   inA    inB |   outY
----------------------
     0      0 |      1
     0      1 |      0
     1      0 |      0
     1      1 |      0

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
**Execution Time:** 0.065s

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
     A      B |    Sum  Carry
-----------------------------
     0      0 |      0      0
     0      1 |      1      0
     1      0 |      1      0
     1      1 |      0      1

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
**Execution Time:** 0.118s

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
     A      B    Cin |    Sum   Cout
------------------------------------
     0      0      0 |      0      0
     0      0      1 |      1      0
     0      1      0 |      1      0
     0      1      1 |      0      1
     1      0      0 |      1      0
     1      0      1 |      0      1
     1      1      0 |      0      1
     1      1      1 |      1      1

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
**Execution Time:** 0.593s

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
     A      B    Cin    Op0    Op1 | Result   Cout
--------------------------------------------------
     0      0      0      0      0 |      0      0
     0      0      0      0      1 |      0      0
     0      0      0      1      0 |      0      0
     0      0      0      1      1 |      0      0
     0      0      1      0      0 |      0      0
     0      0      1      0      1 |      0      0
     0      0      1      1      0 |      0      0
     0      0      1      1      1 |      1      0
     0      1      0      0      0 |      0      0
     0      1      0      0      1 |      1      0
     0      1      0      1      0 |      1      0
     0      1      0      1      1 |      1      0
     0      1      1      0      0 |      0      0
     0      1      1      0      1 |      1      0
     0      1      1      1      0 |      1      0
     0      1      1      1      1 |      0      1
     1      0      0      0      0 |      0      0
     1      0      0      0      1 |      1      0
     1      0      0      1      0 |      1      0
     1      0      0      1      1 |      1      0
     1      0      1      0      0 |      0      0
     1      0      1      0      1 |      1      0
     1      0      1      1      0 |      1      0
     1      0      1      1      1 |      0      1
     1      1      0      0      0 |      1      0
     1      1      0      0      1 |      0      0
     1      1      0      1      0 |      1      0
     1      1      0      1      1 |      0      1
     1      1      1      0      0 |      1      0
     1      1      1      0      1 |      0      0
     1      1      1      1      0 |      1      0
     1      1      1      1      1 |      1      1

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

### 10. 4-bit Adder ✅

**File:** `adder_4bit_bus.sv`
**Description:** 4-bit ripple carry adder using proper SystemVerilog bus notation
**Execution Time:** 4.549s

**Inputs Parsed:** ['A', 'B', 'Cin'] ✅
**Outputs Parsed:** ['Sum', 'Cout'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 13/13 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: adder_4bit_bus.sv
Module: adder_4bit_bus
Inputs: ['A', 'B', 'Cin']
Outputs: ['Sum', 'Cout']
Warning: Too many input combinations (512). Limiting to first 256 combinations.
Truth Table:
A[3:0] B[3:0]    Cin | Sum[3:0]   Cout
--------------------------------------
     0      0      0 |      0      0
     0      0      1 |      1      0
     0      1      0 |      1      0
     0      1      1 |      2      0
     0      2      0 |      2      0
     0      2      1 |      3      0
     0      3      0 |      3      0
     0      3      1 |      4      0
     0      4      0 |      4      0
     0      4      1 |      5      0
     0      5      0 |      5      0
     0      5      1 |      6      0
     0      6      0 |      6      0
     0      6      1 |      7      0
     0      7      0 |      7      0
     0      7      1 |      8      0
     0      8      0 |      8      0
     0      8      1 |      9      0
     0      9      0 |      9      0
     0      9      1 |     10      0
     0     10      0 |     10      0
     0     10      1 |     11      0
     0     11      0 |     11      0
     0     11      1 |     12      0
     0     12      0 |     12      0
     0     12      1 |     13      0
     0     13      0 |     13      0
     0     13      1 |     14      0
     0     14      0 |     14      0
     0     14      1 |     15      0
     0     15      0 |     15      0
     0     15      1 |      0      1
     1      0      0 |      1      0
     1      0      1 |      2      0
     1      1      0 |      2      0
     1      1      1 |      3      0
     1      2      0 |      3      0
     1      2      1 |      4      0
     1      3      0 |      4      0
     1      3      1 |      5      0
     1      4      0 |      5      0
     1      4      1 |      6      0
     1      5      0 |      6      0
     1      5      1 |      7      0
     1      6      0 |      7      0
     1      6      1 |      8      0
     1      7      0 |      8      0
     1      7      1 |      9      0
     1      8      0 |      9      0
     1      8      1 |     10      0
     1      9      0 |     10      0
     1      9      1 |     11      0
     1     10      0 |     11      0
     1     10      1 |     12      0
     1     11      0 |     12      0
     1     11      1 |     13      0
     1     12      0 |     13      0
     1     12      1 |     14      0
     1     13      0 |     14      0
     1     13      1 |     15      0
     1     14      0 |     15      0
     1     14      1 |      0      1
     1     15      0 |      0      1
     1     15      1 |      1      1
     2      0      0 |      2      0
     2      0      1 |      3      0
     2      1      0 |      3      0
     2      1      1 |      4      0
     2      2      0 |      4      0
     2      2      1 |      5      0
     2      3      0 |      5      0
     2      3      1 |      6      0
     2      4      0 |      6      0
     2      4      1 |      7      0
     2      5      0 |      7      0
     2      5      1 |      8      0
     2      6      0 |      8      0
     2      6      1 |      9      0
     2      7      0 |      9      0
     2      7      1 |     10      0
     2      8      0 |     10      0
     2      8      1 |     11      0
     2      9      0 |     11      0
     2      9      1 |     12      0
     2     10      0 |     12      0
     2     10      1 |     13      0
     2     11      0 |     13      0
     2     11      1 |     14      0
     2     12      0 |     14      0
     2     12      1 |     15      0
     2     13      0 |     15      0
     2     13      1 |      0      1
     2     14      0 |      0      1
     2     14      1 |      1      1
     2     15      0 |      1      1
     2     15      1 |      2      1
     3      0      0 |      3      0
     3      0      1 |      4      0
     3      1      0 |      4      0
     3      1      1 |      5      0
     3      2      0 |      5      0
     3      2      1 |      6      0
     3      3      0 |      6      0
     3      3      1 |      7      0
     3      4      0 |      7      0
     3      4      1 |      8      0
     3      5      0 |      8      0
     3      5      1 |      9      0
     3      6      0 |      9      0
     3      6      1 |     10      0
     3      7      0 |     10      0
     3      7      1 |     11      0
     3      8      0 |     11      0
     3      8      1 |     12      0
     3      9      0 |     12      0
     3      9      1 |     13      0
     3     10      0 |     13      0
     3     10      1 |     14      0
     3     11      0 |     14      0
     3     11      1 |     15      0
     3     12      0 |     15      0
     3     12      1 |      0      1
     3     13      0 |      0      1
     3     13      1 |      1      1
     3     14      0 |      1      1
     3     14      1 |      2      1
     3     15      0 |      2      1
     3     15      1 |      3      1
     4      0      0 |      4      0
     4      0      1 |      5      0
     4      1      0 |      5      0
     4      1      1 |      6      0
     4      2      0 |      6      0
     4      2      1 |      7      0
     4      3      0 |      7      0
     4      3      1 |      8      0
     4      4      0 |      8      0
     4      4      1 |      9      0
     4      5      0 |      9      0
     4      5      1 |     10      0
     4      6      0 |     10      0
     4      6      1 |     11      0
     4      7      0 |     11      0
     4      7      1 |     12      0
     4      8      0 |     12      0
     4      8      1 |     13      0
     4      9      0 |     13      0
     4      9      1 |     14      0
     4     10      0 |     14      0
     4     10      1 |     15      0
     4     11      0 |     15      0
     4     11      1 |      0      1
     4     12      0 |      0      1
     4     12      1 |      1      1
     4     13      0 |      1      1
     4     13      1 |      2      1
     4     14      0 |      2      1
     4     14      1 |      3      1
     4     15      0 |      3      1
     4     15      1 |      4      1
     5      0      0 |      5      0
     5      0      1 |      6      0
     5      1      0 |      6      0
     5      1      1 |      7      0
     5      2      0 |      7      0
     5      2      1 |      8      0
     5      3      0 |      8      0
     5      3      1 |      9      0
     5      4      0 |      9      0
     5      4      1 |     10      0
     5      5      0 |     10      0
     5      5      1 |     11      0
     5      6      0 |     11      0
     5      6      1 |     12      0
     5      7      0 |     12      0
     5      7      1 |     13      0
     5      8      0 |     13      0
     5      8      1 |     14      0
     5      9      0 |     14      0
     5      9      1 |     15      0
     5     10      0 |     15      0
     5     10      1 |      0      1
     5     11      0 |      0      1
     5     11      1 |      1      1
     5     12      0 |      1      1
     5     12      1 |      2      1
     5     13      0 |      2      1
     5     13      1 |      3      1
     5     14      0 |      3      1
     5     14      1 |      4      1
     5     15      0 |      4      1
     5     15      1 |      5      1
     6      0      0 |      6      0
     6      0      1 |      7      0
     6      1      0 |      7      0
     6      1      1 |      8      0
     6      2      0 |      8      0
     6      2      1 |      9      0
     6      3      0 |      9      0
     6      3      1 |     10      0
     6      4      0 |     10      0
     6      4      1 |     11      0
     6      5      0 |     11      0
     6      5      1 |     12      0
     6      6      0 |     12      0
     6      6      1 |     13      0
     6      7      0 |     13      0
     6      7      1 |     14      0
     6      8      0 |     14      0
     6      8      1 |     15      0
     6      9      0 |     15      0
     6      9      1 |      0      1
     6     10      0 |      0      1
     6     10      1 |      1      1
     6     11      0 |      1      1
     6     11      1 |      2      1
     6     12      0 |      2      1
     6     12      1 |      3      1
     6     13      0 |      3      1
     6     13      1 |      4      1
     6     14      0 |      4      1
     6     14      1 |      5      1
     6     15      0 |      5      1
     6     15      1 |      6      1
     7      0      0 |      7      0
     7      0      1 |      8      0
     7      1      0 |      8      0
     7      1      1 |      9      0
     7      2      0 |      9      0
     7      2      1 |     10      0
     7      3      0 |     10      0
     7      3      1 |     11      0
     7      4      0 |     11      0
     7      4      1 |     12      0
     7      5      0 |     12      0
     7      5      1 |     13      0
     7      6      0 |     13      0
     7      6      1 |     14      0
     7      7      0 |     14      0
     7      7      1 |     15      0
     7      8      0 |     15      0
     7      8      1 |      0      1
     7      9      0 |      0      1
     7      9      1 |      1      1
     7     10      0 |      1      1
     7     10      1 |      2      1
     7     11      0 |      2      1
     7     11      1 |      3      1
     7     12      0 |      3      1
     7     12      1 |      4      1
     7     13      0 |      4      1
     7     13      1 |      5      1
     7     14      0 |      5      1
     7     14      1 |      6      1
     7     15      0 |      6      1
     7     15      1 |      7      1

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

Test Results: 13/13 passed
All tests passed!

```

---

### 11. 4:1 Multiplexer ✅

**File:** `mux_4to1.sv`
**Description:** 4:1 multiplexer using hierarchical design with bus inputs and select logic
**Execution Time:** 0.444s

**Inputs Parsed:** ['data_in', 'select'] ✅
**Outputs Parsed:** ['out'] ✅
**Truth Table:** Generated ✅
**Test Cases:** 32/32 passed ✅

**Complete Output:**
```
Parsing SystemVerilog file: mux_4to1.sv
Module: mux_4to1
Inputs: ['data_in', 'select']
Outputs: ['out']
Truth Table:
data_in[3:0] select[1:0] |    out
---------------------------------
     0      0 |      0
     0      1 |      0
     0      2 |      0
     0      3 |      0
     1      0 |      1
     1      1 |      0
     1      2 |      0
     1      3 |      0
     2      0 |      0
     2      1 |      1
     2      2 |      0
     2      3 |      0
     3      0 |      1
     3      1 |      1
     3      2 |      0
     3      3 |      0
     4      0 |      0
     4      1 |      0
     4      2 |      1
     4      3 |      0
     5      0 |      1
     5      1 |      0
     5      2 |      1
     5      3 |      0
     6      0 |      0
     6      1 |      1
     6      2 |      1
     6      3 |      0
     7      0 |      1
     7      1 |      1
     7      2 |      1
     7      3 |      0
     8      0 |      0
     8      1 |      0
     8      2 |      0
     8      3 |      1
     9      0 |      1
     9      1 |      0
     9      2 |      0
     9      3 |      1
    10      0 |      0
    10      1 |      1
    10      2 |      0
    10      3 |      1
    11      0 |      1
    11      1 |      1
    11      2 |      0
    11      3 |      1
    12      0 |      0
    12      1 |      0
    12      2 |      1
    12      3 |      1
    13      0 |      1
    13      1 |      0
    13      2 |      1
    13      3 |      1
    14      0 |      0
    14      1 |      1
    14      2 |      1
    14      3 |      1
    15      0 |      1
    15      1 |      1
    15      2 |      1
    15      3 |      1

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

Test Results: 32/32 passed
All tests passed!

```

---

## System Information

- **Python:** 3.13.2 (main, Feb 12 2025, 14:49:53) [MSC v.1942 64 bit (AMD64)]
- **Platform:** win32
- **Working Directory:** C:\Users\jared\pysvsim
- **pysvsim Script:** pysvsim.py