#!/usr/bin/env python3
"""
SystemVerilog Test Runner

A comprehensive testing framework for SystemVerilog files that automatically
discovers and runs JSON test cases, generates truth tables, and produces
detailed test reports with maximum verbosity.

Usage:
    python test_runner.py <file_or_folder>
    
Examples:
    python test_runner.py testing/005-Notgate.sv
    python test_runner.py testing/
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import traceback

# Import our simulator components
from pysvsim import SystemVerilogParser, LogicEvaluator, TruthTableGenerator, clear_module_cache
try:
    from pysvsim import SequentialLogicEvaluator
except ImportError:
    SequentialLogicEvaluator = None
import json
import io
import contextlib

# Silent TestRunner that captures output
class SilentTestRunner:
    """TestRunner that captures all output for clean reporting"""
    
    def __init__(self, evaluator):
        self.evaluator = evaluator
        self.test_outputs = []
        # Check if this is a sequential evaluator
        self.is_sequential = hasattr(evaluator, 'evaluate_cycle')
    
    def load_tests(self, test_file: str):
        """Load test cases from a JSON file."""
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                tests = json.load(f)
            return tests
        except FileNotFoundError:
            raise FileNotFoundError(f"Test file not found: {test_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in test file {test_file}: {e}")
    
    def run_tests(self, tests):
        """Run tests silently and capture results"""
        # Check if this is sequential test format
        if isinstance(tests, dict) and tests.get('test_type') == 'sequential':
            return self._run_sequential_tests(tests)
        else:
            return self._run_combinational_tests(tests)
    
    def _run_combinational_tests(self, tests):
        """Run combinational logic tests (original format)"""
        passed = 0
        total = len(tests)
        self.test_outputs = []
        
        for i, test in enumerate(tests, 1):
            # Extract input values (all keys except 'expect')
            input_values = {k: v for k, v in test.items() if k != "expect"}
            expected_outputs = test.get("expect", {})
            
            # Run simulation
            actual_outputs = self.evaluator.evaluate(input_values)
            
            # Check results
            test_passed = True
            for output_name, expected_value in expected_outputs.items():
                if output_name not in actual_outputs:
                    self.test_outputs.append(f"Test {i} failed: Output '{output_name}' not found")
                    test_passed = False
                elif actual_outputs[output_name] != expected_value:
                    self.test_outputs.append(
                        f"Test {i} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value}"
                    )
                    test_passed = False
            
            if test_passed:
                self.test_outputs.append(f"Test {i} passed")
                passed += 1
        
        return passed, total
    
    def _run_sequential_tests(self, test_data):
        """Run sequential logic tests (new format)"""
        test_cycles = test_data.get('test_cycles', [])
        passed = 0
        total = len(test_cycles)
        self.test_outputs = []
        
        # Reset sequential state
        if hasattr(self.evaluator, 'reset_state'):
            self.evaluator.reset_state()
        
        for i, cycle_test in enumerate(test_cycles):
            cycle_num = cycle_test.get('cycle', i)
            input_values = cycle_test.get('inputs', {})
            expected_outputs = cycle_test.get('expected_outputs', {})
            description = cycle_test.get('description', f'Cycle {cycle_num}')
            
            # Run one clock cycle
            if self.is_sequential:
                actual_outputs = self.evaluator.evaluate_cycle(input_values)
            else:
                # Fallback for combinational evaluator
                actual_outputs = self.evaluator.evaluate(input_values)
            
            # Check results
            test_passed = True
            for output_name, expected_value in expected_outputs.items():
                if output_name not in actual_outputs:
                    self.test_outputs.append(f"Cycle {cycle_num} failed: Output '{output_name}' not found - {description}")
                    test_passed = False
                elif actual_outputs[output_name] != expected_value:
                    self.test_outputs.append(
                        f"Cycle {cycle_num} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value} - {description}"
                    )
                    test_passed = False
            
            if test_passed:
                self.test_outputs.append(f"Cycle {cycle_num} passed - {description}")
                passed += 1
        
        return passed, total


class TestReport:
    """Container for test results and statistics"""
    def __init__(self, sv_file: str):
        self.sv_file = sv_file
        self.json_file = None
        self.success = False
        self.parse_success = False
        self.truth_table_success = False
        self.test_success = False
        self.passed_tests = 0
        self.total_tests = 0
        self.error_message = ""
        self.truth_table = []
        self.evaluator = None
        self.execution_time = 0.0
        self.nand_gate_count = 0
        self.warnings = ""
        self.test_outputs = []
        
    @property
    def has_tests(self) -> bool:
        return self.json_file is not None
        
    @property
    def test_pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100


class SystemVerilogTestRunner:
    """Main test runner for SystemVerilog files and test suites"""
    
    def __init__(self):
        # Fixed settings
        self.max_combinations = 16
        self.continue_on_error = True
        self.reports: List[TestReport] = []
        
    def find_sv_files(self, path: str) -> List[str]:
        """Find all SystemVerilog files in the given path"""
        path_obj = Path(path)
        
        if path_obj.is_file() and path_obj.suffix == '.sv':
            return [str(path_obj)]
        elif path_obj.is_dir():
            return [str(f) for f in path_obj.rglob('*.sv')]
        else:
            raise ValueError(f"Path '{path}' is not a valid file or directory")
    
    def find_json_test(self, sv_file: str) -> Optional[str]:
        """Find the corresponding JSON test file for a SystemVerilog file"""
        sv_path = Path(sv_file)
        json_path = sv_path.with_suffix('.json')
        
        if json_path.exists():
            return str(json_path)
        return None
    
    def test_single_file(self, sv_file: str) -> TestReport:
        """Test a single SystemVerilog file"""
        report = TestReport(sv_file)
        start_time = time.time()
        
        try:
            # Clear module cache to ensure clean state
            clear_module_cache()
            
            # Find JSON test file
            report.json_file = self.find_json_test(sv_file)
            
            # Parse SystemVerilog file
            parser = SystemVerilogParser()
            module_info = parser.parse_file(sv_file)
            report.parse_success = True
            
            # Create evaluator (sequential or combinational based on module content)
            # Check for direct sequential blocks or clock signals
            is_sequential = module_info.get("sequential_blocks") or module_info.get("clock_signals")
            
            # Also check if any instantiated sub-modules are sequential
            if not is_sequential:
                for inst in module_info.get("instantiations", []):
                    module_type = inst["module_type"]
                    # Check for known sequential modules (like register_1bit)
                    if "register" in module_type.lower() or "reg" in module_type.lower():
                        is_sequential = True
                        break
            
            if is_sequential and SequentialLogicEvaluator:
                # Sequential logic detected - use SequentialLogicEvaluator
                evaluator = SequentialLogicEvaluator(
                    module_info["inputs"],
                    module_info["outputs"],
                    module_info["assignments"],
                    module_info.get("instantiations", []),
                    module_info.get("bus_info", {}),
                    module_info.get("slice_assignments", []),
                    module_info.get("concat_assignments", []),
                    module_info.get("sequential_blocks", []),
                    module_info.get("clock_signals", []),
                    sv_file,
                )
            else:
                # Combinational logic - use existing LogicEvaluator
                evaluator = LogicEvaluator(
                    module_info["inputs"],
                    module_info["outputs"],
                    module_info["assignments"],
                    module_info.get("instantiations", []),
                    module_info.get("bus_info", {}),
                    module_info.get("slice_assignments", []),
                    module_info.get("concat_assignments", []),
                    sv_file,
                )
            
            # Store evaluator in report for later use
            report.evaluator = evaluator
            
            # Count NAND gates
            report.nand_gate_count = evaluator.count_nand_gates()
            
            # Generate truth table only for combinational logic (sequential logic truth tables are nonsensical)
            is_sequential = hasattr(evaluator, 'evaluate_cycle')
            if not is_sequential:
                try:
                    # Capture any warning messages during truth table generation
                    f = io.StringIO()
                    with contextlib.redirect_stdout(f):
                        truth_table_gen = TruthTableGenerator(evaluator)
                        report.truth_table = truth_table_gen.generate_truth_table(self.max_combinations)
                    captured_output = f.getvalue()
                    if captured_output.strip():
                        report.warnings = captured_output.strip()
                    report.truth_table_success = True
                except Exception as e:
                    report.error_message = f"Truth table generation failed: {e}"
            else:
                # Skip truth table for sequential logic - it's not meaningful
                report.truth_table_success = True
                report.warnings = "Truth table skipped for sequential logic module"
            
            # Run JSON tests if available
            if report.json_file:
                try:
                    test_runner = SilentTestRunner(evaluator)
                    tests = test_runner.load_tests(report.json_file)
                    
                    # Run tests and get actual counts from the test runner
                    passed, total = test_runner.run_tests(tests)
                    report.passed_tests = passed
                    report.total_tests = total  # Use the actual total from test runner, not len(tests)
                    report.test_success = (passed == total)
                    report.test_outputs = test_runner.test_outputs
                        
                except Exception as e:
                    report.error_message = f"Test execution failed: {str(e)}"
            
            # Overall success
            report.success = (report.parse_success and 
                            (not report.has_tests or report.test_success) and
                            report.truth_table_success)
                            
        except Exception as e:
            report.error_message = f"Parsing failed: {str(e)}"
        
        report.execution_time = time.time() - start_time
        return report
    
    def run_tests(self, path: str) -> None:
        """Run tests for all SystemVerilog files in the given path"""
        try:
            sv_files = self.find_sv_files(path)
            if not sv_files:
                print(f"No SystemVerilog files found in: {path}")
                return
                
            print(f"Found {len(sv_files)} SystemVerilog file(s) to test\n")
            
            for i, sv_file in enumerate(sv_files, 1):
                report = self.test_single_file(sv_file)
                self.reports.append(report)
                
                # Print immediate comprehensive report for this file
                self.print_file_report(report)
                
                # Stop on error if requested
                if not self.continue_on_error and not report.success:
                    print(f"Stopping due to error in: {sv_file}")
                    break
                    
        except KeyboardInterrupt:
            print(f"\n[INFO] Test run interrupted by user")
        except Exception as e:
            print(f"[ERROR] Test runner failed: {e}")
            traceback.print_exc()
    
    def print_file_report(self, report: TestReport) -> None:
        """Print comprehensive report for a single file"""
        print("=" * 80)
        print(f"FILE: {report.sv_file}")
        print("=" * 80)
        
        # Basic info
        status = "PASS" if report.success else "FAIL"
        print(f"Status: [{status}]")
        if report.evaluator and hasattr(report.evaluator, 'module_name'):
            print(f"Module: {report.evaluator.module_name}")
        else:
            # Extract module name from file path as fallback
            module_name = Path(report.sv_file).stem
            print(f"Module: {module_name}")
        print(f"Inputs: {report.evaluator.inputs if report.evaluator else 'N/A'}")
        print(f"Outputs: {report.evaluator.outputs if report.evaluator else 'N/A'}")
        print(f"NAND Gates: {report.nand_gate_count}")
        print(f"Execution Time: {report.execution_time:.3f}s")
        
        # Test results
        if report.has_tests:
            print(f"JSON Test File: {report.json_file}")
            print(f"Test Results: {report.passed_tests}/{report.total_tests} passed ({report.test_pass_rate:.1f}%)")
        else:
            print("JSON Test File: None")
            print("Test Results: No tests")
        
        # Show warnings from truth table generation
        if hasattr(report, 'warnings') and report.warnings:
            print(f"Warnings: {report.warnings}")
        
        # Show test execution details
        if hasattr(report, 'test_outputs') and report.test_outputs:
            print("\nTest Execution:")
            for output in report.test_outputs:
                print(f"  {output}")
        
        # Errors
        if report.error_message:
            print(f"Error: {report.error_message}")
        
        # Truth table - only show for combinational logic
        is_sequential = hasattr(report.evaluator, 'evaluate_cycle') if report.evaluator else False
        if is_sequential:
            print("\nTruth Table: Skipped (sequential logic module)")
        elif report.truth_table and report.truth_table_success and report.evaluator:
            print()
            try:
                truth_table_gen = TruthTableGenerator(report.evaluator)
                truth_table_gen.print_truth_table(report.truth_table)
            except Exception as e:
                print(f"Truth Table Error: {e}")
        elif report.truth_table_success:
            print(f"\nTruth Table: {len(report.truth_table)} combinations generated")
        else:
            print("\nTruth Table: Failed to generate")
        
        print()
        
    def print_detailed_report(self) -> None:
        """Print detailed test report - not used anymore"""
        # This method is kept for compatibility but doesn't do anything
        pass
    
    def print_summary_report(self) -> None:
        """Print summary statistics"""
        total_files = len(self.reports)
        if total_files == 0:
            print("\nNo files tested.")
            return
            
        successful_files = sum(1 for r in self.reports if r.success)
        parse_failures = sum(1 for r in self.reports if not r.parse_success)
        truth_table_failures = sum(1 for r in self.reports if not r.truth_table_success)
        
        files_with_tests = sum(1 for r in self.reports if r.has_tests)
        test_failures = sum(1 for r in self.reports if r.has_tests and not r.test_success)
        total_test_cases = sum(r.total_tests for r in self.reports)
        passed_test_cases = sum(r.passed_tests for r in self.reports)
        
        total_time = sum(r.execution_time for r in self.reports)
        total_nand_gates = sum(r.nand_gate_count for r in self.reports)
        avg_nand_gates = total_nand_gates / total_files if total_files > 0 else 0
        
        print("\n" + "="*60)
        print("SUMMARY REPORT")
        print("="*60)
        print(f"Files Tested:           {total_files}")
        print(f"Overall Success:        {successful_files}/{total_files} ({successful_files/total_files*100:.1f}%)")
        print(f"Parse Failures:         {parse_failures}")
        print(f"Truth Table Failures:   {truth_table_failures}")
        print(f"Files with JSON Tests:  {files_with_tests}")
        print(f"Test Case Failures:     {test_failures}")
        print(f"Total Test Cases:       {total_test_cases}")
        print(f"Passed Test Cases:      {passed_test_cases}/{total_test_cases} ({passed_test_cases/total_test_cases*100 if total_test_cases > 0 else 0:.1f}%)")
        print(f"Total Execution Time:   {total_time:.3f}s")
        print(f"Average Time per File:  {total_time/total_files:.3f}s")
        print(f"Total NAND Gates:       {total_nand_gates}")
        print(f"Average NAND per File:  {avg_nand_gates:.1f}")
        
        # Show failed files
        failed_files = [r for r in self.reports if not r.success]
        if failed_files:
            print(f"\nFailed Files ({len(failed_files)}):")
            for report in failed_files:
                reason = "Parse error" if not report.parse_success else \
                        "Truth table error" if not report.truth_table_success else \
                        "Test failures" if report.has_tests and not report.test_success else \
                        "Unknown error"
                print(f"  [FAIL] {report.sv_file} ({reason})")
        
        print("="*60)


def main():
    """Main entry point for the test runner"""
    # Simple command line argument handling - just expect the path
    if len(sys.argv) != 2:
        print("Usage: python test_runner.py <file_or_folder>")
        print("\nExamples:")
        print("    python test_runner.py testing/005-Notgate.sv")
        print("    python test_runner.py testing/")
        sys.exit(1)
    
    path = sys.argv[1]
    
    # Verify path exists
    if not os.path.exists(path):
        print(f"Error: Path '{path}' does not exist")
        sys.exit(1)
    
    # Create test runner with maximum verbosity settings
    runner = SystemVerilogTestRunner()
    
    print("SystemVerilog Test Runner")
    print("=" * 50)
    print(f"Target: {path}")
    print(f"Max combinations: {runner.max_combinations}")
    print()
    
    # Run tests
    start_time = time.time()
    runner.run_tests(path)
    end_time = time.time()
    
    runner.print_summary_report()
    
    print(f"\nTotal runtime: {end_time - start_time:.3f}s")
    
    # Exit with appropriate code
    failed_files = sum(1 for r in runner.reports if not r.success)
    if failed_files > 0:
        print(f"\nExiting with code 1 ({failed_files} files failed)")
        sys.exit(1)
    else:
        print("\nAll tests passed! Exiting with code 0")
        sys.exit(0)


if __name__ == "__main__":
    main()