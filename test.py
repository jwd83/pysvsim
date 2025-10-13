#!/usr/bin/env python3
"""
Comprehensive Test Suite for pysvsim SystemVerilog Simulator

This script runs all test cases and generates a detailed report of results.
"""

import os
import sys
import json
import subprocess
import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass

# =============================================================================
# TEST CONFIGURATION - Easy to modify test cases
# =============================================================================

@dataclass
class TestCase:
    """Configuration for a single test case."""
    name: str
    verilog_file: str
    test_file: str
    description: str
    expected_inputs: List[str]
    expected_outputs: List[str]

# Test cases to run - modify this list to add/remove tests
TEST_CASES = [
    TestCase(
        name="NAND Gate",
        verilog_file="nand_gate.sv",
        test_file="tests_nand_gate.json",
        description="Basic NAND gate implementation with assign statement",
        expected_inputs=["inA", "inB"],
        expected_outputs=["outY"]
    ),
    TestCase(
        name="Inverter",
        verilog_file="inverter.sv",
        test_file="tests_inverter.json",
        description="Inverter built using NAND gate module instantiation",
        expected_inputs=["in"],
        expected_outputs=["out"]
    ),
    TestCase(
        name="AND Gate",
        verilog_file="and_gate.sv",
        test_file="tests_and_gate.json",
        description="AND gate built from hierarchical NAND + inverter modules",
        expected_inputs=["inA", "inB"],
        expected_outputs=["outY"]
    ),
    TestCase(
        name="OR Gate",
        verilog_file="or_gate.sv",
        test_file="tests_or_gate.json",
        description="OR gate built using De Morgan's law with inverters + NAND",
        expected_inputs=["inA", "inB"],
        expected_outputs=["outY"]
    ),
    TestCase(
        name="XOR Gate",
        verilog_file="xor_gate.sv",
        test_file="tests_xor_gate.json",
        description="XOR gate built using (A & ~B) | (~A & B) with AND/OR/inverter modules",
        expected_inputs=["inA", "inB"],
        expected_outputs=["outY"]
    ),
    TestCase(
        name="NOR Gate",
        verilog_file="nor_gate.sv",
        test_file="tests_nor_gate.json",
        description="NOR gate built using OR gate + inverter (NOT OR)",
        expected_inputs=["inA", "inB"],
        expected_outputs=["outY"]
    ),
    TestCase(
        name="Half Adder",
        verilog_file="half_adder.sv",
        test_file="tests_half_adder.json",
        description="Half adder built from XOR and AND gate modules (hierarchical design)",
        expected_inputs=["A", "B"],
        expected_outputs=["Sum", "Carry"]
    ),
    TestCase(
        name="Full Adder",
        verilog_file="full_adder.sv",
        test_file="tests_full_adder.json",
        description="Full adder built from two half adders with carry chain",
        expected_inputs=["A", "B", "Cin"],
        expected_outputs=["Sum", "Cout"]
    ),
    TestCase(
        name="1-bit ALU",
        verilog_file="alu_1bit.sv",
        test_file="tests_alu_1bit.json",
        description="1-bit ALU slice with 8 operations (AND, OR, XOR, ADD, SUB, NOT, PASS)",
        expected_inputs=["A", "B", "Cin", "Op0", "Op1", "Op2"],
        expected_outputs=["Result", "Cout"]
    ),
    TestCase(
        name="Complex Logic",
        verilog_file="complex_logic.sv",
        test_file=None,  # No test file, just truth table generation
        description="Multi-output module with various bitwise operations",
        expected_inputs=["a", "b", "c"],
        expected_outputs=["out1", "out2", "out3"]
    )
]

# =============================================================================
# TEST EXECUTION AND REPORTING
# =============================================================================

@dataclass
class TestResult:
    """Results of a single test case."""
    test_case: TestCase
    success: bool
    output: str
    error: str
    execution_time: float
    truth_table_generated: bool
    tests_passed: int
    tests_total: int
    inputs_parsed: List[str]
    outputs_parsed: List[str]

class TestRunner:
    """Runs test cases and generates reports."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.pysvsim_script = "pysvsim.py"
        
    def run_all_tests(self) -> List[TestResult]:
        """Run all configured test cases."""
        print("🚀 Starting pysvsim test suite...\n")
        
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"[{i}/{len(TEST_CASES)}] Running {test_case.name}...")
            result = self._run_single_test(test_case)
            self.results.append(result)
            
            if result.success:
                print(f"✅ {test_case.name} passed")
            else:
                print(f"❌ {test_case.name} failed")
            print()
        
        return self.results
    
    def _run_single_test(self, test_case: TestCase) -> TestResult:
        """Run a single test case and capture results."""
        import time
        start_time = time.time()
        
        # Build command
        cmd = ["python", self.pysvsim_script, "--file", test_case.verilog_file]
        if test_case.test_file:
            cmd.extend(["--test", test_case.test_file])
        
        try:
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            execution_time = time.time() - start_time
            
            # Parse output
            output = result.stdout
            error = result.stderr
            success = result.returncode == 0
            
            # Extract information from output
            inputs_parsed, outputs_parsed = self._parse_module_info(output)
            truth_table_generated = "Truth Table:" in output
            tests_passed, tests_total = self._parse_test_results(output)
            
            return TestResult(
                test_case=test_case,
                success=success,
                output=output,
                error=error,
                execution_time=execution_time,
                truth_table_generated=truth_table_generated,
                tests_passed=tests_passed,
                tests_total=tests_total,
                inputs_parsed=inputs_parsed,
                outputs_parsed=outputs_parsed
            )
            
        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            return TestResult(
                test_case=test_case,
                success=False,
                output="",
                error="Test timed out after 30 seconds",
                execution_time=execution_time,
                truth_table_generated=False,
                tests_passed=0,
                tests_total=0,
                inputs_parsed=[],
                outputs_parsed=[]
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_case=test_case,
                success=False,
                output="",
                error=f"Exception: {str(e)}",
                execution_time=execution_time,
                truth_table_generated=False,
                tests_passed=0,
                tests_total=0,
                inputs_parsed=[],
                outputs_parsed=[]
            )
    
    def _parse_module_info(self, output: str) -> Tuple[List[str], List[str]]:
        """Extract input and output information from output."""
        inputs = []
        outputs = []
        
        lines = output.split('\n')
        for line in lines:
            if line.startswith("Inputs: "):
                # Parse: "Inputs: ['inA', 'inB']"
                inputs_str = line.replace("Inputs: ", "").strip()
                try:
                    inputs = eval(inputs_str)  # Safe since we control the format
                except:
                    pass
            elif line.startswith("Outputs: "):
                # Parse: "Outputs: ['outY']"
                outputs_str = line.replace("Outputs: ", "").strip()
                try:
                    outputs = eval(outputs_str)  # Safe since we control the format
                except:
                    pass
        
        return inputs, outputs
    
    def _parse_test_results(self, output: str) -> Tuple[int, int]:
        """Extract test results from output."""
        lines = output.split('\n')
        for line in lines:
            if "Test Results:" in line:
                # Parse: "Test Results: 4/4 passed"
                try:
                    parts = line.split()
                    fraction = parts[2]  # "4/4"
                    passed_str, total_str = fraction.split('/')
                    return int(passed_str), int(total_str)
                except:
                    pass
        return 0, 0
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        report_lines = []
        report_lines.append("# pysvsim Test Report")
        report_lines.append("")
        report_lines.append(f"**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        report_lines.append("## Summary")
        report_lines.append("")
        report_lines.append(f"- **Total Test Cases:** {total_tests}")
        report_lines.append(f"- **Passed:** {passed_tests} ✅")
        report_lines.append(f"- **Failed:** {failed_tests} ❌")
        report_lines.append(f"- **Success Rate:** {(passed_tests/total_tests*100):.1f}%")
        report_lines.append("")
        
        # Individual test results
        report_lines.append("## Test Results")
        report_lines.append("")
        
        for i, result in enumerate(self.results, 1):
            status_emoji = "✅" if result.success else "❌"
            report_lines.append(f"### {i}. {result.test_case.name} {status_emoji}")
            report_lines.append("")
            report_lines.append(f"**File:** `{result.test_case.verilog_file}`")
            report_lines.append(f"**Description:** {result.test_case.description}")
            report_lines.append(f"**Execution Time:** {result.execution_time:.3f}s")
            report_lines.append("")
            
            # Module parsing results
            if result.inputs_parsed:
                inputs_match = result.inputs_parsed == result.test_case.expected_inputs
                inputs_emoji = "✅" if inputs_match else "❌"
                report_lines.append(f"**Inputs Parsed:** {result.inputs_parsed} {inputs_emoji}")
                if not inputs_match:
                    report_lines.append(f"  - Expected: {result.test_case.expected_inputs}")
            
            if result.outputs_parsed:
                outputs_match = result.outputs_parsed == result.test_case.expected_outputs
                outputs_emoji = "✅" if outputs_match else "❌"
                report_lines.append(f"**Outputs Parsed:** {result.outputs_parsed} {outputs_emoji}")
                if not outputs_match:
                    report_lines.append(f"  - Expected: {result.test_case.expected_outputs}")
            
            # Truth table
            if result.truth_table_generated:
                report_lines.append(f"**Truth Table:** Generated ✅")
            else:
                report_lines.append(f"**Truth Table:** Not generated ❌")
            
            # Test cases (if any)
            if result.test_case.test_file:
                if result.tests_total > 0:
                    test_emoji = "✅" if result.tests_passed == result.tests_total else "❌"
                    report_lines.append(f"**Test Cases:** {result.tests_passed}/{result.tests_total} passed {test_emoji}")
                else:
                    report_lines.append(f"**Test Cases:** No test results found ❌")
            else:
                report_lines.append(f"**Test Cases:** No test file specified (truth table only)")
            
            # Error information
            if not result.success:
                report_lines.append("")
                report_lines.append("**Error:**")
                report_lines.append("```")
                if result.error:
                    report_lines.append(result.error)
                else:
                    report_lines.append("Unknown error")
                report_lines.append("```")
            
            # Complete output (no truncation)
            if result.output and result.success:
                lines = result.output.split('\n')
                if lines:
                    report_lines.append("")
                    report_lines.append("**Complete Output:**")
                    report_lines.append("```")
                    report_lines.extend(lines)
                    report_lines.append("```")
            
            report_lines.append("")
            report_lines.append("---")
            report_lines.append("")
        
        # System information
        report_lines.append("## System Information")
        report_lines.append("")
        report_lines.append(f"- **Python:** {sys.version}")
        report_lines.append(f"- **Platform:** {sys.platform}")
        report_lines.append(f"- **Working Directory:** {os.getcwd()}")
        report_lines.append(f"- **pysvsim Script:** {self.pysvsim_script}")
        
        return "\n".join(report_lines)
    
    def save_report(self, filename: str = "report.md"):
        """Save the test report to a file."""
        report_content = self.generate_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print(f"📄 Test report saved to {filename}")

def main():
    """Main function to run tests and generate report."""
    print("pysvsim Test Suite")
    print("=================")
    print()
    
    # Check if pysvsim.py exists
    if not os.path.exists("pysvsim.py"):
        print("❌ Error: pysvsim.py not found in current directory")
        sys.exit(1)
    
    # Run tests
    runner = TestRunner()
    results = runner.run_all_tests()
    
    # Generate and save report
    runner.save_report()
    
    # Print summary
    total = len(results)
    passed = sum(1 for r in results if r.success)
    print(f"\n📊 Final Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check report.md for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()