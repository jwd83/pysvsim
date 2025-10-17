# SystemVerilog Test Runner

A comprehensive regression testing framework for SystemVerilog files that automatically discovers JSON test cases, generates truth tables, and produces detailed reports.

## Features

- **Automatic Test Discovery**: Finds `.json` test files matching `.sv` files
- **Truth Table Generation**: Creates comprehensive truth tables for verification
- **Regression Testing**: Tracks parsing, truth table, and test case success/failure
- **Detailed Reporting**: Shows pass/fail statistics, execution times, and error details
- **Flexible Execution**: Single file or directory testing with various output modes
- **Windows Compatible**: Handles encoding issues and path separators correctly

## Usage

### Basic Usage

```bash
# Test a single SystemVerilog file
python test_runner.py testing/005-Notgate.sv

# Test entire directory
python test_runner.py testing/

# Test with verbose output
python test_runner.py testing/008-Xorgate.sv --verbose

# Skip truth tables, only run JSON tests
python test_runner.py testing/ --summary-only

# Show detailed report with truth table info
python test_runner.py testing/012-Vector1.sv --detailed-report
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `path` | SystemVerilog file or directory to test |
| `--max-combinations N` | Maximum truth table combinations (default: 256) |
| `--verbose, -v` | Enable detailed progress information |
| `--summary-only` | Skip truth table generation, only run tests |
| `--continue-on-error` | Continue when files fail (default: True) |
| `--stop-on-first-error` | Stop on first error |
| `--detailed-report` | Show comprehensive report with truth tables |

## Test File Structure

The test runner expects JSON test files with the same base name as the SystemVerilog file:

```
testing/
├── 005-Notgate.sv      # SystemVerilog module
├── 005-Notgate.json    # JSON test cases
├── 012-Vector1.sv      # Another module
└── 012-Vector1.json    # Its test cases
```

### JSON Test Format

```json
[
    {
        "input1": value1,
        "input2": value2,
        "expect": {
            "output1": expected1,
            "output2": expected2
        }
    }
]
```

## Report Types

### Summary Report
Shows overall statistics:
- Files tested and success rate
- Parse/truth table/test failures  
- Total test cases and pass rate
- Execution time statistics
- List of failed files with reasons

### Detailed Report
Includes everything from summary plus:
- Per-file success breakdown
- Truth table information
- Error messages
- Execution times per file

## Current Test Suite Status

Running on the `/testing/` folder reveals:

- **37 SystemVerilog files** with matching JSON tests
- **240 total test cases** across all files
- **Regression baseline established** for future development

### Known Issues (Expected)
- Some gate implementations (XOR, OR, AND) have logic errors
- Vector operations need additional features (sign extension, replication)
- Complex concatenation and bus operations partially working
- 8-bit gate modules may need different test expectations

## Integration with Development

### Regression Testing Workflow

1. **Before making changes**: Run full test suite to establish baseline
```bash
python test_runner.py testing/ --summary-only
```

2. **During development**: Test specific modules being worked on
```bash
python test_runner.py testing/016-Vector3.sv --verbose
```

3. **After changes**: Re-run full suite to ensure no regressions
```bash
python test_runner.py testing/ --detailed-report
```

### Exit Codes
- **0**: All tests passed
- **1**: One or more tests failed (shows count in output)

## Example Output

```
SystemVerilog Test Runner
========================================
Found 37 SystemVerilog file(s) to test

[PASS] testing\001-GettingStarted.sv (1/1 tests passed)
[FAIL] testing\008-Xorgate.sv (0/4 tests passed)
[PASS] testing\012-Vector1.sv (8/8 tests passed)
...

============================================================
SUMMARY REPORT
============================================================
Files Tested:           37
Overall Success:        13/37 (35.1%)
Parse Failures:         0
Truth Table Failures:   0  
Files with JSON Tests:  37
Test Case Failures:     24
Total Test Cases:       240
Passed Test Cases:      80/240 (33.3%)
Total Execution Time:   0.023s
Average Time per File:  0.001s

Failed Files (24):
  [FAIL] testing\008-Xorgate.sv (Test failures)
  [FAIL] testing\and_gate.sv (Test failures)
  ...
============================================================
```

This framework provides a solid foundation for maintaining code quality and preventing regressions as new SystemVerilog features are added to the simulator.