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
import io
import contextlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing


def _check_missing_expect_fields(tests) -> str:
    """Check if any test cases are missing expect/expected fields.

    Returns a warning message if any tests are missing expect fields, empty string otherwise.
    """
    missing_count = 0

    if isinstance(tests, dict):
        if tests.get('test_type') == 'sequential':
            # Old sequential format
            for cycle in tests.get('test_cycles', []):
                if not cycle.get('expected_outputs'):
                    missing_count += 1
        elif tests.get('sequential') or tests.get('test_cases'):
            # New sequential format
            for test_case in tests.get('test_cases', []):
                if 'sequence' in test_case:
                    for step in test_case['sequence']:
                        if not step.get('expected'):
                            missing_count += 1
                elif not test_case.get('expected'):
                    missing_count += 1
    elif isinstance(tests, list):
        # Old combinational format
        for test in tests:
            if not test.get('expect'):
                missing_count += 1

    if missing_count > 0:
        return f"Warning: {missing_count} test(s) missing expect field"
    return ""


def _append_warning(existing: str, new_warning: str) -> str:
    """Append a warning message using the existing semicolon-delimited format."""
    if not new_warning:
        return existing
    if existing:
        return f"{existing}; {new_warning}"
    return new_warning


# Import our simulator components
from pysvsim import (
    SystemVerilogParser,
    TruthTableGenerator,
    clear_module_cache,
    create_evaluator,
    TestRunner as SimulatorTestRunner,
)
from pysvsim import TruthTableImageGenerator, WaveformImageGenerator

def _find_json_test_file(sv_file: str) -> Optional[str]:
    """Find the corresponding JSON test file for a SystemVerilog file."""
    sv_path = Path(sv_file)
    possible_names = [
        sv_path.with_suffix(".json"),
        sv_path.parent / f"{sv_path.stem}_test.json",
        sv_path.parent / f"{sv_path.stem}_tests.json",
    ]
    for json_path in possible_names:
        if json_path.exists():
            return str(json_path)
    return None


def _generate_truth_table(evaluator, max_combinations: int) -> Tuple[List[Dict[str, int]], bool, str]:
    """Generate a truth table and capture any warning output."""
    truth_table: List[Dict[str, int]] = []
    truth_table_success = True
    warnings = ""

    if hasattr(evaluator, "evaluate_cycle"):
        return truth_table, True, "Truth table skipped for sequential logic module"

    try:
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            truth_table_gen = TruthTableGenerator(evaluator)
            truth_table = truth_table_gen.generate_truth_table(max_combinations)
        warnings = capture.getvalue().strip()
    except Exception as e:
        truth_table_success = False
        warnings = f"Truth table generation failed: {e}"

    return truth_table, truth_table_success, warnings


def _run_json_tests(evaluator, json_file: str) -> Dict[str, Any]:
    """Run JSON-backed tests using the shared simulator-side test runner."""
    sim_runner = SimulatorTestRunner(evaluator, verbose=False)
    tests = sim_runner.load_tests(json_file)
    missing_expect_warning = _check_missing_expect_fields(tests)
    passed_tests, total_tests = sim_runner.run_tests(tests)
    return {
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "test_success": passed_tests == total_tests,
        "test_outputs": sim_runner.test_outputs,
        "test_cycles": sim_runner.test_cycles,
        "warning": missing_expect_warning,
    }


def _generate_output_image(
    evaluator,
    sv_file: str,
    truth_table: List[Dict[str, int]],
    test_cycles: List[Dict[str, Any]],
) -> Tuple[Optional[str], str]:
    """Generate the PNG artifact associated with a file's results."""
    try:
        png_path = str(Path(sv_file).with_suffix(".png"))
        if hasattr(evaluator, "evaluate_cycle"):
            if test_cycles:
                waveform_gen = WaveformImageGenerator(evaluator)
                waveform_gen.generate_image(test_cycles, png_path)
                return png_path, ""
            return None, ""

        if truth_table:
            image_gen = TruthTableImageGenerator(evaluator)
            image_gen.generate_image(truth_table, png_path)
            return png_path, ""
    except Exception as e:
        return None, f"Image generation failed: {e}"

    return None, ""


def _analyze_sv_file(sv_file: str, max_combinations: int = 16) -> Dict[str, Any]:
    """Process one SystemVerilog file into a serializable result payload."""
    try:
        start_time = time.time()
        clear_module_cache()

        json_file = _find_json_test_file(sv_file)
        parser = SystemVerilogParser()
        module_info = parser.parse_file(sv_file)
        evaluator = create_evaluator(module_info, filepath=sv_file, check_submodules=True)
        nand_gate_count = evaluator.count_nand_gates()

        truth_table, truth_table_success, warnings = _generate_truth_table(
            evaluator, max_combinations
        )
        test_cycles: List[Dict[str, Any]] = []
        passed_tests = 0
        total_tests = 0
        test_success = True
        test_outputs: List[str] = []
        error_message = ""

        if json_file:
            try:
                test_result = _run_json_tests(evaluator, json_file)
                passed_tests = test_result["passed_tests"]
                total_tests = test_result["total_tests"]
                test_success = test_result["test_success"]
                test_outputs = test_result["test_outputs"]
                test_cycles = test_result["test_cycles"]
                warnings = _append_warning(warnings, test_result["warning"])
            except Exception as e:
                test_success = False
                error_message = f"Test execution failed: {e}"
                test_outputs = []

        png_file, image_warning = _generate_output_image(
            evaluator, sv_file, truth_table, test_cycles
        )
        warnings = _append_warning(warnings, image_warning)
        execution_time = time.time() - start_time

        return {
            "sv_file": sv_file,
            "json_file": json_file,
            "success": truth_table_success and (not json_file or test_success),
            "parse_success": True,
            "truth_table_success": truth_table_success,
            "test_success": test_success,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "error_message": error_message,
            "truth_table": truth_table,
            "execution_time": execution_time,
            "nand_gate_count": nand_gate_count,
            "warnings": warnings,
            "test_outputs": test_outputs,
            "inputs": module_info["inputs"],
            "outputs": module_info["outputs"],
            "bus_info": module_info.get("bus_info", {}),
            "png_file": png_file,
            "module_name": module_info.get("name", Path(sv_file).stem),
            "is_sequential": hasattr(evaluator, "evaluate_cycle"),
        }
    except Exception as e:
        return {
            "sv_file": sv_file,
            "json_file": None,
            "success": False,
            "parse_success": False,
            "truth_table_success": False,
            "test_success": False,
            "passed_tests": 0,
            "total_tests": 0,
            "error_message": f"Processing failed: {e}",
            "truth_table": [],
            "execution_time": 0.0,
            "nand_gate_count": 0,
            "warnings": "",
            "test_outputs": [],
            "inputs": [],
            "outputs": [],
            "bus_info": {},
            "png_file": None,
            "module_name": Path(sv_file).stem,
            "is_sequential": False,
        }


def test_single_file_standalone(sv_file: str, max_combinations: int = 16):
    """Standalone function to test a single file - used for parallel processing."""
    return _analyze_sv_file(sv_file, max_combinations)


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
        self.png_file = None
        self.module_name = Path(sv_file).stem
        self.is_sequential = False
        
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
    
    def __init__(self, parallel=True, max_workers=None):
        # Fixed settings
        self.max_combinations = 16
        self.continue_on_error = True
        self.reports: List[TestReport] = []
        self.parallel = parallel
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
        self.run_failed = False
        self.run_failure_message = ""
        
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
        return _find_json_test_file(sv_file)

    def _report_from_result(self, result_dict: Dict[str, Any]) -> TestReport:
        """Convert a serializable result payload into a TestReport."""
        report = TestReport(result_dict["sv_file"])
        report.json_file = result_dict["json_file"]
        report.success = result_dict["success"]
        report.parse_success = result_dict["parse_success"]
        report.truth_table_success = result_dict["truth_table_success"]
        report.test_success = result_dict["test_success"]
        report.passed_tests = result_dict["passed_tests"]
        report.total_tests = result_dict["total_tests"]
        report.error_message = result_dict["error_message"]
        report.truth_table = result_dict["truth_table"]
        report.execution_time = result_dict["execution_time"]
        report.nand_gate_count = result_dict["nand_gate_count"]
        report.warnings = result_dict["warnings"]
        report.test_outputs = result_dict["test_outputs"]
        report.png_file = result_dict.get("png_file")
        report.module_name = result_dict.get("module_name", report.module_name)
        report.is_sequential = result_dict.get("is_sequential", False)

        class DummyEvaluator:
            def __init__(self, inputs, outputs, bus_info, module_name):
                self.inputs = inputs
                self.outputs = outputs
                self.bus_info = bus_info or {}
                self.module_name = module_name

        report.evaluator = DummyEvaluator(
            result_dict.get("inputs", []),
            result_dict.get("outputs", []),
            result_dict.get("bus_info", {}),
            report.module_name,
        )
        return report

    def test_single_file(self, sv_file: str) -> TestReport:
        """Test a single SystemVerilog file."""
        return self._report_from_result(_analyze_sv_file(sv_file, self.max_combinations))
    
    def run_tests(self, path: str) -> None:
        """Run tests for all SystemVerilog files in the given path"""
        self.run_failed = False
        self.run_failure_message = ""
        try:
            sv_files = self.find_sv_files(path)
            if not sv_files:
                print(f"No SystemVerilog files found in: {path}")
                return
                
            print(f"Found {len(sv_files)} SystemVerilog file(s) to test\n")
            
            if self.parallel and len(sv_files) > 1:
                try:
                    self._run_tests_parallel(sv_files)
                except Exception as e:
                    # Fall back when the host disallows process workers.
                    print(f"[WARN] Parallel execution unavailable: {e}")
                    print("[INFO] Falling back to sequential execution\n")
                    self._run_tests_sequential(sv_files)
            else:
                self._run_tests_sequential(sv_files)
                    
        except KeyboardInterrupt:
            self.run_failed = True
            self.run_failure_message = "Test run interrupted by user"
            print(f"\n[INFO] Test run interrupted by user")
        except Exception as e:
            self.run_failed = True
            self.run_failure_message = str(e)
            print(f"[ERROR] Test runner failed: {e}")
            traceback.print_exc()
    
    def _run_tests_sequential(self, sv_files: List[str]) -> None:
        """Run tests sequentially (original behavior)"""
        for i, sv_file in enumerate(sv_files, 1):
            report = self.test_single_file(sv_file)
            self.reports.append(report)
            
            # Print immediate comprehensive report for this file
            self.print_file_report(report)
            
            # Stop on error if requested
            if not self.continue_on_error and not report.success:
                print(f"Stopping due to error in: {sv_file}")
                break
    
    def _run_tests_parallel(self, sv_files: List[str]) -> None:
        """Run tests in parallel using ProcessPoolExecutor"""
        print(f"Running tests in parallel with {self.max_workers} workers...\n")
        
        # Submit all tasks to the process pool
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs and maintain order mapping
            future_to_index = {}
            for i, sv_file in enumerate(sv_files):
                future = executor.submit(test_single_file_standalone, sv_file, self.max_combinations)
                future_to_index[future] = i
            
            # Collect results as they complete, but store by original index
            reports_by_index = {}
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                sv_file = sv_files[index]
                try:
                    reports_by_index[index] = self._report_from_result(future.result())
                    
                except Exception as e:
                    # Create error report for failed job
                    error_report = TestReport(sv_file)
                    error_report.error_message = f"Parallel execution failed: {str(e)}"
                    reports_by_index[index] = error_report
            
            # Print reports in original file order
            ordered_reports = []
            for i in range(len(sv_files)):
                report = reports_by_index[i]
                ordered_reports.append(report)
                self.print_file_report(report)
            
            # Store all reports in correct order
            self.reports.extend(ordered_reports)
    
    def print_file_report(self, report: TestReport) -> None:
        """Print comprehensive report for a single file"""
        print("=" * 80)
        print(f"FILE: {report.sv_file}")
        print("=" * 80)
        
        # Basic info
        status = "PASS" if report.success else "FAIL"
        print(f"Status: [{status}]")
        print(f"Module: {report.module_name}")
        print(f"Inputs: {report.evaluator.inputs if report.evaluator else 'N/A'}")
        print(f"Outputs: {report.evaluator.outputs if report.evaluator else 'N/A'}")
        print(f"NAND Gates: {report.nand_gate_count}")
        print(f"Execution Time: {report.execution_time:.3f}s")
        if hasattr(report, 'png_file') and report.png_file:
            print(f"PNG Output: {report.png_file}")

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
        if report.is_sequential:
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
            if self.run_failed and self.run_failure_message:
                print(f"Run failure: {self.run_failure_message}")
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
        if self.run_failed and self.run_failure_message:
            print(f"Run Failure:            {self.run_failure_message}")
        
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
    import argparse
    
    parser = argparse.ArgumentParser(
        description="SystemVerilog Test Runner with parallel processing support",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("path", help="SystemVerilog file or directory to test")
    parser.add_argument("--sequential", "-s", action="store_true", 
                       help="Run tests sequentially instead of in parallel")
    parser.add_argument("--workers", "-w", type=int, 
                       help="Number of parallel workers (default: CPU count - 1)")
    parser.add_argument("--max-combinations", "-c", type=int, default=16,
                       help="Maximum truth table combinations to test (default: 16)")
    
    args = parser.parse_args()
    
    # Verify path exists
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist")
        sys.exit(1)
    
    # Create test runner
    parallel = not args.sequential
    runner = SystemVerilogTestRunner(parallel=parallel, max_workers=args.workers)
    runner.max_combinations = args.max_combinations
    
    print("SystemVerilog Test Runner")
    print("=" * 50)
    print(f"Target: {args.path}")
    print(f"Max combinations: {runner.max_combinations}")
    if parallel:
        print(f"Parallel processing: {runner.max_workers} workers")
    else:
        print("Running sequentially")
    print()
    
    # Run tests
    start_time = time.time()
    runner.run_tests(args.path)
    end_time = time.time()
    
    runner.print_summary_report()
    
    print(f"\nTotal runtime: {end_time - start_time:.3f}s")
    
    # Exit with appropriate code
    failed_files = sum(1 for r in runner.reports if not r.success)
    if runner.run_failed:
        print(f"\nExiting with code 1 ({runner.run_failure_message})")
        sys.exit(1)
    if failed_files > 0:
        print(f"\nExiting with code 1 ({failed_files} files failed)")
        sys.exit(1)
    else:
        print("\nAll tests passed! Exiting with code 0")
        sys.exit(0)


if __name__ == "__main__":
    main()
