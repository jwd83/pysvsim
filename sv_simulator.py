#!/usr/bin/env python3
"""
SystemVerilog Simulator for Game Development

A pure Python SystemVerilog simulator that parses basic combinational logic
modules and generates truth tables. Supports testing with JSON test cases.

Usage:
    python sv_simulator.py --file <verilog_file> [--test <json_file>] [--max-combinations N]
"""

import argparse
import json
import re
import sys
from typing import Dict, List, Tuple, Any, Optional
from itertools import product


class SystemVerilogParser:
    """Parser for a subset of SystemVerilog focused on basic combinational logic."""
    
    def __init__(self):
        self.module_name = ""
        self.inputs = []
        self.outputs = []
        self.wires = []
        self.assignments = {}
        self.instantiations = []
    
    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a SystemVerilog file and extract module information.
        
        Args:
            filepath: Path to the .sv file
            
        Returns:
            Dictionary containing module info: name, inputs, outputs, assignments
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"SystemVerilog file not found: {filepath}")
        except Exception as e:
            raise Exception(f"Error reading file {filepath}: {e}")
        
        return self._parse_content(content)
    
    def _parse_content(self, content: str) -> Dict[str, Any]:
        """Parse the SystemVerilog content and extract module components."""
        # Remove comments and clean up
        content = self._remove_comments(content)
        content = ' '.join(content.split())  # Normalize whitespace
        
        # Extract module declaration
        module_match = re.search(r'module\s+(\w+)\s*\((.*?)\)\s*;', content, re.DOTALL)
        if not module_match:
            raise ValueError("No valid module declaration found")
        
        self.module_name = module_match.group(1)
        port_list = module_match.group(2)
        
        # Parse ports
        self._parse_ports(content, port_list)
        
        # Parse wire declarations
        self._parse_wires(content)
        
        # Parse assign statements
        self._parse_assignments(content)
        
        # Parse module instantiations
        self._parse_instantiations(content)
        
        return {
            'name': self.module_name,
            'inputs': self.inputs.copy(),
            'outputs': self.outputs.copy(),
            'assignments': self.assignments.copy(),
            'instantiations': self.instantiations.copy()
        }
    
    def _remove_comments(self, content: str) -> str:
        """Remove single-line (//) and multi-line (/* */) comments."""
        # Remove single-line comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        return content
    
    def _parse_ports(self, content: str, port_list: str):
        """Parse input and output port declarations."""
        # Find all input/output declarations in the module
        port_declarations = re.findall(r'(input|output)\s+(\w+)', content)
        
        for port_type, port_name in port_declarations:
            if port_type == 'input':
                self.inputs.append(port_name)
            elif port_type == 'output':
                self.outputs.append(port_name)
    
    def _parse_wires(self, content: str):
        """Parse wire declarations."""
        wire_pattern = r'wire\s+(\w+)\s*;'
        wires = re.findall(wire_pattern, content)
        self.wires.extend(wires)
    
    def _parse_assignments(self, content: str):
        """Parse assign statements and build assignment expressions."""
        assign_pattern = r'assign\s+(\w+)\s*=\s*([^;]+)\s*;'
        assignments = re.findall(assign_pattern, content)
        
        for output_signal, expression in assignments:
            # Clean up the expression
            expression = expression.strip()
            self.assignments[output_signal] = expression
    
    def _parse_instantiations(self, content: str):
        """Parse module instantiations."""
        # Pattern to match module instantiations like: module_name instance_name ( port connections );
        inst_pattern = r'(\w+)\s+(\w+)\s*\((.*?)\)\s*;'
        instantiations = re.findall(inst_pattern, content)
        
        for module_type, instance_name, connections in instantiations:
            # Skip if this looks like a module declaration
            if module_type == 'module':
                continue
                
            # Parse port connections
            port_connections = {}
            # Pattern to match .port_name(signal_name) connections
            conn_pattern = r'\.([\w]+)\(([\w]+)\)'
            connections_found = re.findall(conn_pattern, connections)
            
            for port_name, signal_name in connections_found:
                port_connections[port_name] = signal_name
            
            self.instantiations.append({
                'module_type': module_type,
                'instance_name': instance_name,
                'connections': port_connections
            })


class LogicEvaluator:
    """Evaluates SystemVerilog expressions with given input values."""
    
    def __init__(self, inputs: List[str], outputs: List[str], assignments: Dict[str, str], instantiations: List[Dict[str, Any]] = None):
        self.inputs = inputs
        self.outputs = outputs
        self.assignments = assignments
        self.instantiations = instantiations or []
        self.loaded_modules = {}  # Cache for loaded modules
    
    def evaluate(self, input_values: Dict[str, int]) -> Dict[str, int]:
        """
        Evaluate all output expressions for given input values.
        
        Args:
            input_values: Dictionary mapping input names to their values (0 or 1)
            
        Returns:
            Dictionary mapping output names to their computed values
        """
        # Start with input values
        signal_values = input_values.copy()
        
        # Evaluate module instantiations first
        for inst in self.instantiations:
            self._evaluate_instantiation(inst, signal_values)
        
        # Evaluate each assignment
        output_values = {}
        for output_name in self.outputs:
            if output_name in self.assignments:
                expression = self.assignments[output_name]
                value = self._evaluate_expression(expression, signal_values)
                output_values[output_name] = value
                signal_values[output_name] = value
            elif output_name in signal_values:  # Output from instantiation
                output_values[output_name] = signal_values[output_name]
        
        return output_values
    
    def _evaluate_expression(self, expression: str, signal_values: Dict[str, int]) -> int:
        """Evaluate a single SystemVerilog expression."""
        # Replace signal names with their values
        eval_expr = expression
        
        # Handle parentheses and operators in correct precedence
        # For now, we'll use a simple approach with string replacement
        for signal_name, value in signal_values.items():
            eval_expr = re.sub(r'\b' + re.escape(signal_name) + r'\b', str(value), eval_expr)
        
        # Convert SystemVerilog operators to Python equivalents
        eval_expr = self._convert_operators(eval_expr)
        
        try:
            # Evaluate the expression safely
            result = eval(eval_expr)
            return int(result) & 1  # Ensure single bit result
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}': {e}")
    
    def _convert_operators(self, expression: str) -> str:
        """Convert SystemVerilog operators to Python equivalents."""
        # Handle bitwise NOT
        expression = re.sub(r'~', '~', expression)
        # Handle bitwise AND
        expression = re.sub(r'&', '&', expression)
        # Handle bitwise OR
        expression = re.sub(r'\|', '|', expression)
        # Handle bitwise XOR
        expression = re.sub(r'\^', '^', expression)
        
        return expression
    
    def _evaluate_instantiation(self, inst: Dict[str, Any], signal_values: Dict[str, int]):
        """Evaluate a module instantiation."""
        module_type = inst['module_type']
        connections = inst['connections']
        
        # Load the referenced module if not already loaded
        if module_type not in self.loaded_modules:
            self._load_module(module_type)
        
        if module_type not in self.loaded_modules:
            raise ValueError(f"Could not load module '{module_type}'")
        
        module_info = self.loaded_modules[module_type]
        
        # Build input values for the instantiated module
        inst_input_values = {}
        for port_name, signal_name in connections.items():
            if port_name in module_info['inputs']:
                if signal_name in signal_values:
                    inst_input_values[port_name] = signal_values[signal_name]
                else:
                    raise ValueError(f"Signal '{signal_name}' not found for instantiation '{inst['instance_name']}'")
        
        # Create evaluator for the instantiated module
        inst_evaluator = LogicEvaluator(
            module_info['inputs'],
            module_info['outputs'],
            module_info['assignments'],
            module_info.get('instantiations', [])
        )
        
        # Evaluate the instantiated module
        inst_outputs = inst_evaluator.evaluate(inst_input_values)
        
        # Map outputs back to the parent module's signals
        for port_name, signal_name in connections.items():
            if port_name in module_info['outputs']:
                signal_values[signal_name] = inst_outputs[port_name]
    
    def _load_module(self, module_name: str):
        """Load a module from file."""
        import os
        
        # Try to find the module file in the current directory
        module_file = f"{module_name}.sv"
        if os.path.exists(module_file):
            try:
                parser = SystemVerilogParser()
                module_info = parser.parse_file(module_file)
                self.loaded_modules[module_name] = module_info
            except Exception as e:
                print(f"Warning: Could not load module '{module_name}': {e}")


class TruthTableGenerator:
    """Generates and displays truth tables for combinational logic."""
    
    def __init__(self, evaluator: LogicEvaluator):
        self.evaluator = evaluator
    
    def generate_truth_table(self, max_combinations: int = 16) -> List[Dict[str, int]]:
        """
        Generate truth table for all input combinations.
        
        Args:
            max_combinations: Maximum number of input combinations to test
            
        Returns:
            List of dictionaries containing input and output values for each combination
        """
        inputs = self.evaluator.inputs
        num_inputs = len(inputs)
        
        # Limit combinations if too many inputs
        if 2**num_inputs > max_combinations:
            print(f"Warning: Too many input combinations ({2**num_inputs}). "
                  f"Limiting to first {max_combinations} combinations.")
        
        truth_table = []
        combinations_to_test = min(2**num_inputs, max_combinations)
        
        for i in range(combinations_to_test):
            # Convert index to binary representation
            input_values = {}
            for j, input_name in enumerate(inputs):
                bit_value = (i >> (num_inputs - 1 - j)) & 1
                input_values[input_name] = bit_value
            
            # Evaluate outputs
            output_values = self.evaluator.evaluate(input_values)
            
            # Combine inputs and outputs
            row = {**input_values, **output_values}
            truth_table.append(row)
        
        return truth_table
    
    def print_truth_table(self, truth_table: List[Dict[str, int]]):
        """Print a formatted truth table."""
        if not truth_table:
            print("No truth table data to display.")
            return
        
        inputs = self.evaluator.inputs
        outputs = self.evaluator.outputs
        
        # Print header
        header_inputs = " ".join(f"{inp:>3}" for inp in inputs)
        header_outputs = " ".join(f"{out:>3}" for out in outputs)
        print("Truth Table:")
        print(f"{header_inputs} | {header_outputs}")
        print("-" * (len(header_inputs) + 3 + len(header_outputs)))
        
        # Print data rows
        for row in truth_table:
            input_values = " ".join(f"{row[inp]:>3}" for inp in inputs)
            output_values = " ".join(f"{row[out]:>3}" for out in outputs)
            print(f"{input_values} | {output_values}")


class TestRunner:
    """Runs test cases from JSON files against the simulator."""
    
    def __init__(self, evaluator: LogicEvaluator):
        self.evaluator = evaluator
    
    def load_tests(self, test_file: str) -> List[Dict[str, Any]]:
        """Load test cases from a JSON file."""
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                tests = json.load(f)
            return tests
        except FileNotFoundError:
            raise FileNotFoundError(f"Test file not found: {test_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in test file {test_file}: {e}")
    
    def run_tests(self, tests: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Run all test cases and return pass/fail counts.
        
        Args:
            tests: List of test case dictionaries
            
        Returns:
            Tuple of (passed_count, total_count)
        """
        print("\nRunning tests...")
        passed = 0
        total = len(tests)
        
        for i, test in enumerate(tests, 1):
            # Extract input values (all keys except 'expect')
            input_values = {k: v for k, v in test.items() if k != 'expect'}
            expected_outputs = test.get('expect', {})
            
            # Run simulation
            actual_outputs = self.evaluator.evaluate(input_values)
            
            # Check results
            test_passed = True
            for output_name, expected_value in expected_outputs.items():
                if output_name not in actual_outputs:
                    print(f"✗ Test {i} failed: Output '{output_name}' not found")
                    test_passed = False
                elif actual_outputs[output_name] != expected_value:
                    print(f"✗ Test {i} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value}")
                    test_passed = False
            
            if test_passed:
                print(f"✓ Test {i} passed")
                passed += 1
        
        return passed, total


def main():
    """Main function to run the SystemVerilog simulator."""
    parser = argparse.ArgumentParser(
        description="SystemVerilog Simulator for Game Development",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--file', required=True, help='SystemVerilog file to simulate')
    parser.add_argument('--test', help='JSON test file (optional)')
    parser.add_argument('--max-combinations', type=int, default=16, 
                       help='Maximum number of input combinations to test (default: 16)')
    
    args = parser.parse_args()
    
    try:
        # Parse SystemVerilog file
        print(f"Parsing SystemVerilog file: {args.file}")
        sv_parser = SystemVerilogParser()
        module_info = sv_parser.parse_file(args.file)
        
        print(f"Module: {module_info['name']}")
        print(f"Inputs: {module_info['inputs']}")
        print(f"Outputs: {module_info['outputs']}")
        
        # Create evaluator
        evaluator = LogicEvaluator(
            module_info['inputs'], 
            module_info['outputs'], 
            module_info['assignments'],
            module_info.get('instantiations', [])
        )
        
        # Generate and display truth table
        truth_table_gen = TruthTableGenerator(evaluator)
        truth_table = truth_table_gen.generate_truth_table(args.max_combinations)
        truth_table_gen.print_truth_table(truth_table)
        
        # Run tests if provided
        if args.test:
            test_runner = TestRunner(evaluator)
            tests = test_runner.load_tests(args.test)
            passed, total = test_runner.run_tests(tests)
            
            print(f"\nTest Results: {passed}/{total} passed")
            if passed == total:
                print("All tests passed! ✓")
            else:
                print(f"{total - passed} test(s) failed.")
                sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()