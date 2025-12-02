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


def test_single_file_standalone(sv_file: str, max_combinations: int = 16):
    """Standalone function to test a single file - used for parallel processing"""
    import json
    import os
    import sys
    import time
    from pathlib import Path
    import io
    import contextlib
    
    try:
        # Import here to avoid issues with multiprocessing
        from pysvsim import SystemVerilogParser, LogicEvaluator, TruthTableGenerator, clear_module_cache
        try:
            from pysvsim import SequentialLogicEvaluator
        except ImportError:
            SequentialLogicEvaluator = None
        
        # Inline simplified version of test logic to avoid circular imports
        start_time = time.time()
        
        # Clear module cache
        clear_module_cache()
        
        # Find JSON test file
        sv_path = Path(sv_file)
        possible_names = [
            sv_path.with_suffix('.json'),
            sv_path.parent / f"{sv_path.stem}_test.json",
            sv_path.parent / f"{sv_path.stem}_tests.json",
        ]
        json_file = None
        for json_path in possible_names:
            if json_path.exists():
                json_file = str(json_path)
                break
        
        # Parse SystemVerilog file
        parser = SystemVerilogParser()
        module_info = parser.parse_file(sv_file)
        
        # Create evaluator
        is_sequential = module_info.get("sequential_blocks") or module_info.get("clock_signals")
        if not is_sequential:
            for inst in module_info.get("instantiations", []):
                module_type = inst["module_type"]
                if "register" in module_type.lower() or "reg" in module_type.lower():
                    is_sequential = True
                    break
        
        if is_sequential and SequentialLogicEvaluator:
            evaluator = SequentialLogicEvaluator(
                module_info["inputs"], module_info["outputs"], module_info["assignments"],
                module_info.get("instantiations", []), module_info.get("bus_info", {}),
                module_info.get("slice_assignments", []), module_info.get("concat_assignments", []),
                module_info.get("sequential_blocks", []), module_info.get("clock_signals", []), sv_file
            )
        else:
            evaluator = LogicEvaluator(
                module_info["inputs"], module_info["outputs"], module_info["assignments"],
                module_info.get("instantiations", []), module_info.get("bus_info", {}),
                module_info.get("slice_assignments", []), module_info.get("concat_assignments", []), sv_file
            )
        
        # Count NAND gates
        nand_count = evaluator.count_nand_gates()
        
        # Generate truth table for combinational logic
        truth_table = []
        truth_table_success = True
        warnings = ""
        is_sequential_eval = hasattr(evaluator, 'evaluate_cycle')
        
        if not is_sequential_eval:
            try:
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    truth_table_gen = TruthTableGenerator(evaluator)
                    truth_table = truth_table_gen.generate_truth_table(max_combinations)
                captured_output = f.getvalue()
                if captured_output.strip():
                    warnings = captured_output.strip()
            except Exception as e:
                truth_table_success = False
                warnings = f"Truth table generation failed: {e}"
        else:
            warnings = "Truth table skipped for sequential logic module"
        
        # Run tests if available
        passed_tests = 0
        total_tests = 0
        test_success = True
        test_outputs = []
        
        if json_file:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    tests = json.load(f)
                
                # Check for missing expect fields and warn
                missing_expect_warning = _check_missing_expect_fields(tests)
                if missing_expect_warning:
                    if warnings:
                        warnings += "; " + missing_expect_warning
                    else:
                        warnings = missing_expect_warning
                
                # Run tests using simplified logic
                if isinstance(tests, dict) and tests.get('test_type') == 'sequential':
                    # Old sequential format
                    test_cycles = tests.get('test_cycles', [])
                    if hasattr(evaluator, 'reset_state'):
                        evaluator.reset_state()
                    
                    for i, cycle_test in enumerate(test_cycles):
                        cycle_num = cycle_test.get('cycle', i)
                        input_values = cycle_test.get('inputs', {})
                        expected_outputs = cycle_test.get('expected_outputs', {})
                        description = cycle_test.get('description', f'Cycle {cycle_num}')
                        
                        # Run one clock cycle
                        if hasattr(evaluator, 'evaluate_cycle'):
                            actual_outputs = evaluator.evaluate_cycle(input_values)
                        else:
                            actual_outputs = evaluator.evaluate(input_values)
                        
                        # Check results
                        test_passed = True
                        for output_name, expected_value in expected_outputs.items():
                            if output_name not in actual_outputs or actual_outputs[output_name] != expected_value:
                                test_passed = False
                                break
                        
                        if test_passed:
                            test_outputs.append(f"Cycle {cycle_num} passed - {description}")
                            passed_tests += 1
                        else:
                            test_outputs.append(f"Cycle {cycle_num} failed - {description}")
                        total_tests += 1
                
                elif isinstance(tests, dict) and (tests.get('sequential') or tests.get('test_cases')):
                    # New sequential format
                    test_cases = tests.get('test_cases', [])
                    if hasattr(evaluator, 'reset_state'):
                        evaluator.reset_state()
                    
                    for test_case in test_cases:
                        name = test_case.get('name', 'Unnamed test')
                        if 'sequence' in test_case:
                            sequence_passed = True
                            for step in test_case['sequence']:
                                input_values = step.get('inputs', {})
                                expected_outputs = step.get('expected', {})
                                
                                if hasattr(evaluator, 'evaluate_cycle'):
                                    actual_outputs = evaluator.evaluate_cycle(input_values)
                                else:
                                    actual_outputs = evaluator.evaluate(input_values)
                                
                                for output_name, expected_value in expected_outputs.items():
                                    if output_name not in actual_outputs or actual_outputs[output_name] != expected_value:
                                        sequence_passed = False
                                        break
                                if not sequence_passed:
                                    break
                            
                            if sequence_passed:
                                test_outputs.append(f"{name} passed")
                                passed_tests += 1
                            else:
                                test_outputs.append(f"{name} failed")
                            total_tests += 1
                        else:
                            # Single test case
                            input_values = test_case.get('inputs', {})
                            expected_outputs = test_case.get('expected', {})
                            
                            if hasattr(evaluator, 'evaluate_cycle'):
                                actual_outputs = evaluator.evaluate_cycle(input_values)
                            else:
                                actual_outputs = evaluator.evaluate(input_values)
                            
                            test_passed = True
                            for output_name, expected_value in expected_outputs.items():
                                if output_name not in actual_outputs or actual_outputs[output_name] != expected_value:
                                    test_passed = False
                                    break
                            
                            if test_passed:
                                test_outputs.append(f"{name} passed")
                                passed_tests += 1
                            else:
                                test_outputs.append(f"{name} failed")
                            total_tests += 1
                
                else:
                    # Old combinational format
                    for i, test in enumerate(tests, 1):
                        input_values = {k: v for k, v in test.items() if k != "expect"}
                        expected_outputs = test.get("expect", {})
                        
                        actual_outputs = evaluator.evaluate(input_values)
                        
                        test_passed = True
                        for output_name, expected_value in expected_outputs.items():
                            if output_name not in actual_outputs or actual_outputs[output_name] != expected_value:
                                test_passed = False
                                break
                        
                        if test_passed:
                            test_outputs.append(f"Test {i} passed")
                            passed_tests += 1
                        else:
                            test_outputs.append(f"Test {i} failed")
                        total_tests += 1
                
                test_success = (passed_tests == total_tests)
                
            except Exception as e:
                test_success = False
                test_outputs = [f"Test execution failed: {str(e)}"]
        
        execution_time = time.time() - start_time
        
        # Return dictionary instead of TestReport object to avoid serialization issues
        return {
            'sv_file': sv_file,
            'json_file': json_file,
            'success': truth_table_success and (not json_file or test_success),
            'parse_success': True,
            'truth_table_success': truth_table_success,
            'test_success': test_success,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'error_message': '',
            'truth_table': truth_table,
            'execution_time': execution_time,
            'nand_gate_count': nand_count,
            'warnings': warnings,
            'test_outputs': test_outputs,
            'inputs': module_info["inputs"],
            'outputs': module_info["outputs"],
            'bus_info': module_info.get("bus_info", {})
        }
        
    except Exception as e:
        return {
            'sv_file': sv_file,
            'json_file': None,
            'success': False,
            'parse_success': False,
            'truth_table_success': False,
            'test_success': False,
            'passed_tests': 0,
            'total_tests': 0,
            'error_message': f"Parallel processing failed: {str(e)}",
            'truth_table': [],
            'execution_time': 0.0,
            'nand_gate_count': 0,
            'warnings': '',
            'test_outputs': [],
            'inputs': [],
            'outputs': [],
            'bus_info': {}
        }


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
        # Check if this is the new sequential test format
        if isinstance(tests, dict) and (tests.get('sequential') or tests.get('test_cases')):
            return self._run_new_sequential_tests(tests)
        # Check if this is the old sequential test format
        elif isinstance(tests, dict) and tests.get('test_type') == 'sequential':
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
    
    def _run_new_sequential_tests(self, test_data):
        """Run new sequential logic tests format"""
        test_cases = test_data.get('test_cases', [])
        passed = 0
        total = 0
        self.test_outputs = []
        
        # Reset sequential state if available
        if hasattr(self.evaluator, 'reset_state'):
            self.evaluator.reset_state()
        
        for test_case in test_cases:
            name = test_case.get('name', 'Unnamed test')
            
            if 'sequence' in test_case:
                # Handle sequence tests
                sequence_passed = True
                for step in test_case['sequence']:
                    input_values = step.get('inputs', {})
                    expected_outputs = step.get('expected', {})
                    
                    # Run one clock cycle
                    if self.is_sequential:
                        actual_outputs = self.evaluator.evaluate_cycle(input_values)
                    else:
                        actual_outputs = self.evaluator.evaluate(input_values)
                    
                    # Check results for this step
                    for output_name, expected_value in expected_outputs.items():
                        if output_name not in actual_outputs:
                            self.test_outputs.append(f"{name} failed: Output '{output_name}' not found")
                            sequence_passed = False
                        elif actual_outputs[output_name] != expected_value:
                            self.test_outputs.append(
                                f"{name} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value}"
                            )
                            sequence_passed = False
                
                if sequence_passed:
                    self.test_outputs.append(f"{name} passed")
                    passed += 1
                total += 1
            
            else:
                # Handle single test cases
                input_values = test_case.get('inputs', {})
                expected_outputs = test_case.get('expected', {})
                
                # Run one clock cycle
                if self.is_sequential:
                    actual_outputs = self.evaluator.evaluate_cycle(input_values)
                else:
                    actual_outputs = self.evaluator.evaluate(input_values)
                
                # Check results
                test_passed = True
                for output_name, expected_value in expected_outputs.items():
                    if output_name not in actual_outputs:
                        self.test_outputs.append(f"{name} failed: Output '{output_name}' not found")
                        test_passed = False
                    elif actual_outputs[output_name] != expected_value:
                        self.test_outputs.append(
                            f"{name} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value}"
                        )
                        test_passed = False
                
                if test_passed:
                    self.test_outputs.append(f"{name} passed")
                    passed += 1
                total += 1
        
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
    
    def __init__(self, parallel=True, max_workers=None):
        # Fixed settings
        self.max_combinations = 16
        self.continue_on_error = True
        self.reports: List[TestReport] = []
        self.parallel = parallel
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
        
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
        
        # Try different naming patterns
        possible_names = [
            sv_path.with_suffix('.json'),  # Original: counter8.json
            sv_path.parent / f"{sv_path.stem}_test.json",  # New: counter8_test.json
            sv_path.parent / f"{sv_path.stem}_tests.json",  # Alternative: counter8_tests.json
        ]
        
        for json_path in possible_names:
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
            
            if self.parallel and len(sv_files) > 1:
                self._run_tests_parallel(sv_files)
            else:
                self._run_tests_sequential(sv_files)
                    
        except KeyboardInterrupt:
            print(f"\n[INFO] Test run interrupted by user")
        except Exception as e:
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
                    result_dict = future.result()
                    # Convert dictionary back to TestReport object
                    report = TestReport(result_dict['sv_file'])
                    report.json_file = result_dict['json_file']
                    report.success = result_dict['success']
                    report.parse_success = result_dict['parse_success']
                    report.truth_table_success = result_dict['truth_table_success']
                    report.test_success = result_dict['test_success']
                    report.passed_tests = result_dict['passed_tests']
                    report.total_tests = result_dict['total_tests']
                    report.error_message = result_dict['error_message']
                    report.truth_table = result_dict['truth_table']
                    report.execution_time = result_dict['execution_time']
                    report.nand_gate_count = result_dict['nand_gate_count']
                    report.warnings = result_dict['warnings']
                    report.test_outputs = result_dict['test_outputs']
                    
                    # Create a dummy evaluator with the basic info for reporting
                    class DummyEvaluator:
                        def __init__(self, inputs, outputs, bus_info):
                            self.inputs = inputs
                            self.outputs = outputs
                            self.bus_info = bus_info or {}
                    
                    report.evaluator = DummyEvaluator(result_dict['inputs'], result_dict['outputs'], result_dict.get('bus_info', {}))
                    reports_by_index[index] = report
                    
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
    if failed_files > 0:
        print(f"\nExiting with code 1 ({failed_files} files failed)")
        sys.exit(1)
    else:
        print("\nAll tests passed! Exiting with code 0")
        sys.exit(0)


if __name__ == "__main__":
    main()