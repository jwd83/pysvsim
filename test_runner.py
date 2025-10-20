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
from pysvsim import SystemVerilogParser, LogicEvaluator, TruthTableGenerator, TestRunner, clear_module_cache


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
        # Fixed settings for maximum verbosity
        self.max_combinations = 16
        self.verbose = True
        self.summary_only = False
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
            
            if self.verbose:
                print(f"\n[INFO] Testing {sv_file}")
                if report.json_file:
                    print(f"[INFO] Using test file: {report.json_file}")
                else:
                    print("[INFO] No JSON test file found")
            
            # Parse SystemVerilog file
            parser = SystemVerilogParser()
            module_info = parser.parse_file(sv_file)
            report.parse_success = True
            
            if self.verbose:
                print(f"[INFO] Parsed module: {module_info['name']}")
                print(f"[INFO] Inputs: {module_info['inputs']}")
                print(f"[INFO] Outputs: {module_info['outputs']}")
            
            # Create evaluator
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
            
            if self.verbose:
                print(f"[INFO] NAND Gate Count: {report.nand_gate_count}")
            
            # Generate truth table if requested
            if not self.summary_only:
                try:
                    truth_table_gen = TruthTableGenerator(evaluator)
                    report.truth_table = truth_table_gen.generate_truth_table(self.max_combinations)
                    report.truth_table_success = True
                    
                    if self.verbose:
                        print(f"[INFO] Generated truth table with {len(report.truth_table)} combinations")
                except Exception as e:
                    if self.verbose:
                        print(f"[WARN] Truth table generation failed: {e}")
            
            # Run JSON tests if available
            if report.json_file:
                try:
                    test_runner = TestRunner(evaluator)
                    tests = test_runner.load_tests(report.json_file)
                    report.total_tests = len(tests)
                    
                    passed, total = test_runner.run_tests(tests)
                    report.passed_tests = passed
                    report.test_success = (passed == total)
                    
                    if self.verbose:
                        print(f"[INFO] Test results: {passed}/{total} passed")
                        
                except Exception as e:
                    report.error_message = f"Test execution failed: {str(e)}"
                    if self.verbose:
                        print(f"[ERROR] {report.error_message}")
            
            # Overall success
            report.success = (report.parse_success and 
                            (not report.has_tests or report.test_success) and
                            (self.summary_only or report.truth_table_success))
                            
        except Exception as e:
            report.error_message = f"Parsing failed: {str(e)}"
            if self.verbose:
                print(f"[ERROR] {report.error_message}")
                traceback.print_exc()
        
        report.execution_time = time.time() - start_time
        return report
    
    def run_tests(self, path: str) -> None:
        """Run tests for all SystemVerilog files in the given path"""
        try:
            sv_files = self.find_sv_files(path)
            if not sv_files:
                print(f"No SystemVerilog files found in: {path}")
                return
                
            print(f"Found {len(sv_files)} SystemVerilog file(s) to test")
            
            for i, sv_file in enumerate(sv_files, 1):
                report = self.test_single_file(sv_file)
                self.reports.append(report)
                
                # Print progress
                if not self.verbose:
                    status = "[PASS]" if report.success else "[FAIL]"
                    test_info = ""
                    if report.has_tests:
                        test_info = f" ({report.passed_tests}/{report.total_tests} tests passed)"
                    print(f"{status} {sv_file}{test_info}")
                
                # Stop on error if requested
                if not self.continue_on_error and not report.success:
                    print(f"Stopping due to error in: {sv_file}")
                    break
                    
        except KeyboardInterrupt:
            print("\n[INFO] Test run interrupted by user")
        except Exception as e:
            print(f"[ERROR] Test runner failed: {e}")
            traceback.print_exc()
    
    def print_detailed_report(self) -> None:
        """Print detailed test report including truth tables"""
        print("\n" + "="*80)
        print("DETAILED TEST REPORT")
        print("="*80)
        
        for report in self.reports:
            print(f"\nFile: {report.sv_file}")
            print("-" * 60)
            print(f"Parse Success: {'[PASS]' if report.parse_success else '[FAIL]'}")
            print(f"Truth Table:   {'[PASS]' if report.truth_table_success else '[FAIL]'}")
            
            if report.has_tests:
                print(f"JSON Tests:    {report.json_file}")
                print(f"Test Success:  {'[PASS]' if report.test_success else '[FAIL]'}")
                print(f"Tests Passed:  {report.passed_tests}/{report.total_tests} ({report.test_pass_rate:.1f}%)")
            else:
                print("JSON Tests:    No test file found")
            
            print(f"Execution Time: {report.execution_time:.3f}s")
            print(f"NAND Gate Count: {report.nand_gate_count}")
            
            if report.error_message:
                print(f"Error: {report.error_message}")
            
            # Print truth table if available and verbose mode
            if self.verbose and report.truth_table and report.truth_table_success and report.evaluator:
                try:
                    # Create truth table generator and print the formatted table
                    truth_table_gen = TruthTableGenerator(report.evaluator)
                    print("\n")  # Add some spacing
                    truth_table_gen.print_truth_table(report.truth_table)
                except Exception as e:
                    print(f"\nTruth Table: {len(report.truth_table)} combinations generated (formatting error: {e})")
    
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
    
    print("SystemVerilog Test Runner (Maximum Verbosity)")
    print("=" * 50)
    print(f"Target: {path}")
    print(f"Max combinations: {runner.max_combinations}")
    print("Mode: Full verbose output with detailed reports")
    print()
    
    # Run tests
    start_time = time.time()
    runner.run_tests(path)
    end_time = time.time()
    
    # Always print detailed report since we want maximum verbosity
    runner.print_detailed_report()
    
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