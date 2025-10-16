#!/usr/bin/env python3
"""
SystemVerilog Simulator for Game Development

A pure Python SystemVerilog simulator that parses basic combinational logic
modules and generates truth tables. Supports testing with JSON test cases.

Usage:
    python pysvsim.py --file <verilog_file> [--test <json_file>] [--max-combinations N]

Defaults to 256 max combinations for comprehensive truth table generation.
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
        self.bus_info = {}  # Track bus widths and ranges
        self.assignments = {}
        self.instantiations = []
        self.filepath = ""

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a SystemVerilog file and extract module information.

        Args:
            filepath: Path to the .sv file

        Returns:
            Dictionary containing module info: name, inputs, outputs, assignments
        """
        self.filepath = filepath
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
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
        content = " ".join(content.split())  # Normalize whitespace

        # Extract module declaration
        module_match = re.search(r"module\s+(\w+)\s*\((.*?)\)\s*;", content, re.DOTALL)
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
            "name": self.module_name,
            "inputs": self.inputs.copy(),
            "outputs": self.outputs.copy(),
            "assignments": self.assignments.copy(),
            "instantiations": self.instantiations.copy(),
            "bus_info": self.bus_info.copy(),
        }

    def _remove_comments(self, content: str) -> str:
        """Remove single-line (//) and multi-line (/* */) comments."""
        # Remove single-line comments
        content = re.sub(r"//.*$", "", content, flags=re.MULTILINE)
        # Remove multi-line comments
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        return content

    def _parse_ports(self, content: str, port_list: str):
        """Parse input and output port declarations, including buses."""
        # First, try to parse from the port list in the module declaration
        # This handles cases where ports are declared in the module header
        self._parse_port_list(port_list)

        # Port list parsing is complete. Additional port declarations in module body
        # would be for internal signals, not module ports, so we skip content-based
        # port parsing to avoid conflicts.

    def _parse_port_list(self, port_list: str):
        """Parse the port list from the module declaration header."""
        # Remove extra whitespace and handle multi-line declarations
        port_list = " ".join(port_list.split())

        # Parse by finding all input/output sections
        # Split the port list into sections starting with input or output
        sections = []
        current_section = ""
        current_type = None

        # Tokenize the port list, including 'wire' and 'logic' keywords which can appear after input/output
        tokens = re.findall(r"\b(?:input|output|wire|logic)\b|\[[^\]]+\]|\w+|,", port_list)

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ["input", "output"]:
                # Save previous section if exists
                if current_type and current_section:
                    self._parse_port_section(current_type, current_section)

                # Start new section
                current_type = token
                current_section = ""
            elif token in ["wire", "logic"]:
                # Skip 'wire' and 'logic' keywords - they're optional and don't affect functionality
                pass
            elif token.startswith("[") and token.endswith("]"):
                # Bus specification
                current_section += " " + token
            elif token == ",":
                # Comma separator
                current_section += token
            elif token.isalnum() or "_" in token:
                # Signal name
                current_section += " " + token

            i += 1

        # Process the last section
        if current_type and current_section:
            self._parse_port_section(current_type, current_section)

    def _parse_port_section(self, port_type: str, section: str):
        """Parse a single port section (input or output)."""
        section = section.strip()

        # Check if this is a bus declaration
        bus_match = re.match(r"\s*\[(\d+):(\d+)\]\s*(.+)", section)
        if bus_match:
            # Bus declaration
            msb, lsb, port_names = bus_match.groups()
            msb, lsb = int(msb), int(lsb)
            width = abs(msb - lsb) + 1

            # Parse signal names
            names = [name.strip() for name in port_names.split(",") if name.strip()]

            for port_name in names:
                self.bus_info[port_name] = {"msb": msb, "lsb": lsb, "width": width}

                if port_type == "input":
                    self.inputs.append(port_name)
                elif port_type == "output":
                    self.outputs.append(port_name)
        else:
            # Single-bit declarations
            names = [name.strip() for name in section.split(",") if name.strip()]

            for port_name in names:
                if port_name not in self.bus_info:
                    self.bus_info[port_name] = {"msb": 0, "lsb": 0, "width": 1}

                    if port_type == "input":
                        self.inputs.append(port_name)
                    elif port_type == "output":
                        self.outputs.append(port_name)

    def _parse_wires(self, content: str):
        """Parse wire declarations, including bus wires."""
        # Handle bus wire declarations like: wire [3:0] temp;
        bus_wire_pattern = r"wire\s+\[(\d+):(\d+)\]\s+(\w+)\s*;"
        bus_wire_declarations = re.findall(bus_wire_pattern, content)

        for msb, lsb, wire_name in bus_wire_declarations:
            msb, lsb = int(msb), int(lsb)
            width = abs(msb - lsb) + 1
            self.bus_info[wire_name] = {"msb": msb, "lsb": lsb, "width": width}
            self.wires.append(wire_name)

        # Handle single-bit wire declarations like: wire temp1, temp2;
        single_wire_pattern = r"wire\s+(?!\[)([\w,\s]+)\s*;"
        single_wire_declarations = re.findall(single_wire_pattern, content)

        for wire_list in single_wire_declarations:
            # Split by comma and clean up whitespace
            wires = [wire.strip() for wire in wire_list.split(",") if wire.strip()]
            for wire_name in wires:
                if wire_name not in self.bus_info:
                    self.bus_info[wire_name] = {"msb": 0, "lsb": 0, "width": 1}
                    self.wires.append(wire_name)

    def _parse_assignments(self, content: str):
        """Parse assign statements and build assignment expressions."""
        # Enhanced pattern to capture bus slice assignments like out_hi[7:0] = in[15:8]
        assign_pattern = r"assign\s+([\w\[\]:]+)\s*=\s*([^;]+)\s*;"
        assignments = re.findall(assign_pattern, content)

        for output_signal, expression in assignments:
            # Clean up the expression
            expression = expression.strip()

            # Extract base signal name from bus slice notation like out_hi[7:0]
            base_signal_match = re.match(r"(\w+)(?:\[\d+:\d+\])?", output_signal)
            if base_signal_match:
                base_signal = base_signal_match.group(1)
                self.assignments[base_signal] = expression
            else:
                self.assignments[output_signal] = expression

    def _parse_instantiations(self, content: str):
        """Parse module instantiations."""
        # Pattern to match module instantiations like: module_name instance_name ( port connections );
        inst_pattern = r"(\w+)\s+(\w+)\s*\((.*?)\)\s*;"
        instantiations = re.findall(inst_pattern, content)

        for module_type, instance_name, connections in instantiations:
            # Skip if this looks like a module declaration
            if module_type == "module":
                continue

            # Parse port connections
            port_connections = {}
            # Pattern to match .port_name(signal_name) connections including bit selections like A[0] and bus slices like A[3:0]
            conn_pattern = r"\.([\w]+)\(([\w\[\]:]+)\)"
            connections_found = re.findall(conn_pattern, connections)

            for port_name, signal_name in connections_found:
                port_connections[port_name] = signal_name

            self.instantiations.append(
                {
                    "module_type": module_type,
                    "instance_name": instance_name,
                    "connections": port_connections,
                }
            )


class LogicEvaluator:
    """Evaluates SystemVerilog expressions with given input values."""

    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        assignments: Dict[str, str],
        instantiations: List[Dict[str, Any]] = None,
        bus_info: Dict[str, Dict] = None,
    ):
        self.inputs = inputs
        self.outputs = outputs
        self.assignments = assignments
        self.instantiations = instantiations or []
        self.bus_info = bus_info or {}
        self.loaded_modules = {}  # Cache for loaded modules

    def evaluate(self, input_values: Dict[str, int]) -> Dict[str, int]:
        """
        Evaluate all output expressions for given input values.

        Args:
            input_values: Dictionary mapping input names to their values (buses as integers)

        Returns:
            Dictionary mapping output names to their computed values
        """
        # Start with input values and expand buses to individual bits
        signal_values = {}
        for signal_name, value in input_values.items():
            signal_values[signal_name] = value
            # If this is a bus, also create individual bit signals
            if signal_name in self.bus_info:
                bus_info = self.bus_info[signal_name]
                if bus_info["width"] > 1:
                    self._expand_bus_to_bits(signal_name, value, signal_values)

        # Evaluate module instantiations first
        for inst in self.instantiations:
            self._evaluate_instantiation(inst, signal_values)

        # Evaluate all assignments (including intermediate wires) until no more changes
        # This handles cases where assignments depend on each other
        max_iterations = len(self.assignments) + 10  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            changed = False
            iteration += 1

            for signal_name, expression in self.assignments.items():
                try:
                    new_value = self._evaluate_expression(expression, signal_values)
                    if (
                        signal_name not in signal_values
                        or signal_values[signal_name] != new_value
                    ):
                        signal_values[signal_name] = new_value
                        changed = True
                        # If this is a bus, expand to individual bits
                        if (
                            signal_name in self.bus_info
                            and self.bus_info[signal_name]["width"] > 1
                        ):
                            self._expand_bus_to_bits(
                                signal_name, new_value, signal_values
                            )
                except:
                    # Skip assignments that can't be evaluated yet (dependencies not ready)
                    continue

            # If no changes were made, we're done
            if not changed:
                break

        # Extract output values
        output_values = {}
        for output_name in self.outputs:
            if output_name in signal_values:
                output_values[output_name] = signal_values[output_name]
            else:
                # Check if this is a bus that needs to be collected from individual bits
                if (
                    output_name in self.bus_info
                    and self.bus_info[output_name]["width"] > 1
                ):
                    bus_value = self._collect_bus_from_bits(output_name, signal_values)
                    output_values[output_name] = bus_value
                    signal_values[output_name] = bus_value

        return output_values

    def _evaluate_expression(
        self, expression: str, signal_values: Dict[str, int]
    ) -> int:
        """Evaluate a single SystemVerilog expression."""
        # Replace signal names with their values
        eval_expr = expression.strip()

        # Handle simple bus-to-bus assignment (like Y = A)
        if eval_expr in signal_values:
            return signal_values[eval_expr]

        # Handle bus slice expressions like A[7:0], in[15:8] first
        bus_slice_pattern = r"(\w+)\[(\d+):(\d+)\]"

        def replace_bus_slice(match):
            bus_name = match.group(1)
            msb = int(match.group(2))
            lsb = int(match.group(3))

            # Extract the bus value
            if bus_name in signal_values:
                bus_value = signal_values[bus_name]
                # Extract the specified bits
                width = abs(msb - lsb) + 1
                shift = lsb if msb >= lsb else msb
                mask = (1 << width) - 1
                slice_value = (bus_value >> shift) & mask
                return str(slice_value)
            return match.group(0)  # Return original if not found

        eval_expr = re.sub(bus_slice_pattern, replace_bus_slice, eval_expr)

        # Handle single bus bit selection like A[2], B[0]
        bit_select_pattern = r"(\w+)\[(\d+)\]"

        def replace_bit_select(match):
            bus_name = match.group(1)
            bit_index = int(match.group(2))
            bit_signal = f"{bus_name}[{bit_index}]"
            if bit_signal in signal_values:
                return str(signal_values[bit_signal])
            return match.group(0)  # Return original if not found

        eval_expr = re.sub(bit_select_pattern, replace_bit_select, eval_expr)

        # Handle parentheses and operators in correct precedence
        # For now, we'll use a simple approach with string replacement
        for signal_name, value in signal_values.items():
            # Skip bit selection signals as they're already handled above
            if "[" not in signal_name:
                eval_expr = re.sub(
                    r"\b" + re.escape(signal_name) + r"\b", str(value), eval_expr
                )

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
        expression = re.sub(r"~", "~", expression)
        # Handle bitwise AND
        expression = re.sub(r"&", "&", expression)
        # Handle bitwise OR
        expression = re.sub(r"\|", "|", expression)
        # Handle bitwise XOR
        expression = re.sub(r"\^", "^", expression)

        return expression

    def _evaluate_instantiation(
        self, inst: Dict[str, Any], signal_values: Dict[str, int]
    ):
        """Evaluate a module instantiation."""
        module_type = inst["module_type"]
        connections = inst["connections"]

        # Load the referenced module if not already loaded
        if module_type not in self.loaded_modules:
            self._load_module(module_type)

        if module_type not in self.loaded_modules:
            raise ValueError(f"Could not load module '{module_type}'")

        module_info = self.loaded_modules[module_type]

        # Build input values for the instantiated module
        inst_input_values = {}
        for port_name, signal_name in connections.items():
            if port_name in module_info["inputs"]:
                signal_value = None

                # Handle direct signal reference
                if signal_name in signal_values:
                    signal_value = signal_values[signal_name]
                else:
                    # Check if it's a bus slice like A[3:0]
                    bus_slice_match = re.match(r"(\w+)\[(\d+):(\d+)\]", signal_name)
                    if bus_slice_match:
                        bus_name = bus_slice_match.group(1)
                        msb = int(bus_slice_match.group(2))
                        lsb = int(bus_slice_match.group(3))
                        
                        if bus_name in signal_values:
                            # Extract the bus slice from the parent bus
                            bus_value = signal_values[bus_name]
                            width = abs(msb - lsb) + 1
                            shift = lsb if msb >= lsb else msb
                            mask = (1 << width) - 1
                            signal_value = (bus_value >> shift) & mask
                    else:
                        # Check if it's a bit selection like A[0]
                        bit_select_match = re.match(r"(\w+)\[(\d+)\]", signal_name)
                        if bit_select_match:
                            bus_name = bit_select_match.group(1)
                            bit_index = int(bit_select_match.group(2))
                            bit_signal_name = f"{bus_name}[{bit_index}]"
                            if bit_signal_name in signal_values:
                                signal_value = signal_values[bit_signal_name]

                if signal_value is not None:
                    inst_input_values[port_name] = signal_value
                else:
                    raise ValueError(
                        f"Signal '{signal_name}' not found for instantiation '{inst['instance_name']}'"
                    )

        # Create evaluator for the instantiated module
        inst_evaluator = LogicEvaluator(
            module_info["inputs"],
            module_info["outputs"],
            module_info["assignments"],
            module_info.get("instantiations", []),
            module_info.get("bus_info", {}),
        )

        # Evaluate the instantiated module
        inst_outputs = inst_evaluator.evaluate(inst_input_values)

        # Map outputs back to the parent module's signals
        for port_name, signal_name in connections.items():
            if port_name in module_info["outputs"]:
                # Check if it's a bus slice assignment like outSum[3:0]
                bus_slice_match = re.match(r"(\w+)\[(\d+):(\d+)\]", signal_name)
                if bus_slice_match:
                    bus_name = bus_slice_match.group(1)
                    msb = int(bus_slice_match.group(2))
                    lsb = int(bus_slice_match.group(3))
                    output_value = inst_outputs[port_name]
                    
                    # Initialize bus if not exists
                    if bus_name not in signal_values:
                        signal_values[bus_name] = 0
                    
                    # Update the specific slice of the bus
                    width = abs(msb - lsb) + 1
                    shift = lsb if msb >= lsb else msb
                    mask = (1 << width) - 1
                    
                    # Clear the target bits and set new value
                    signal_values[bus_name] = (signal_values[bus_name] & ~(mask << shift)) | ((output_value & mask) << shift)
                    
                    # Also expand this updated bus to individual bits for consistency
                    if bus_name in self.bus_info and self.bus_info[bus_name]["width"] > 1:
                        self._expand_bus_to_bits(bus_name, signal_values[bus_name], signal_values)
                else:
                    # Handle direct signal assignment
                    signal_values[signal_name] = inst_outputs[port_name]

                    # Also handle bit selection assignment like Sum[0]
                    bit_select_match = re.match(r"(\w+)\[(\d+)\]", signal_name)
                    if bit_select_match:
                        bus_name = bit_select_match.group(1)
                        bit_index = int(bit_select_match.group(2))
                        bit_signal_name = f"{bus_name}[{bit_index}]"
                        signal_values[bit_signal_name] = inst_outputs[port_name]

    def _expand_bus_to_bits(
        self, bus_name: str, bus_value: int, signal_values: Dict[str, int]
    ):
        """Expand a bus value into individual bit signals."""
        bus_info = self.bus_info[bus_name]
        msb, lsb = bus_info["msb"], bus_info["lsb"]

        # Create individual bit signals like A[3], A[2], A[1], A[0] for a 4-bit bus
        for i in range(max(msb, lsb), min(msb, lsb) - 1, -1):
            bit_index = abs(i - lsb) if msb >= lsb else abs(lsb - i)
            bit_value = (bus_value >> bit_index) & 1
            signal_values[f"{bus_name}[{i}]"] = bit_value

    def _collect_bus_from_bits(
        self, bus_name: str, signal_values: Dict[str, int]
    ) -> int:
        """Collect individual bit signals back into a bus value."""
        bus_info = self.bus_info[bus_name]
        msb, lsb = bus_info["msb"], bus_info["lsb"]
        bus_value = 0

        for i in range(max(msb, lsb), min(msb, lsb) - 1, -1):
            bit_index = abs(i - lsb) if msb >= lsb else abs(lsb - i)
            bit_name = f"{bus_name}[{i}]"
            if bit_name in signal_values:
                bus_value |= (signal_values[bit_name] & 1) << bit_index

        return bus_value

    def _load_module(self, module_name: str):
        """Load a module from file."""
        import os

        # Try to find the module file in the current directory
        module_file = f"{module_name}.sv"

        load_file = False
        if os.path.exists(module_file):
            load_file = True
            # print(f"Loading module '{module_name}' from current directory")
        else:
            # look for module in the same folder as the main file being simulated
            module_file = os.path.join(os.path.dirname(gargs.file), f"{module_name}.sv")
            if os.path.exists(module_file):
                load_file = True
                # print(f"Loading module '{module_name}' from {module_file}")
            # print(f"Looking for module '{module_name}' in {module_file}")
        if load_file:
            try:
                parser = SystemVerilogParser()
                module_info = parser.parse_file(module_file)
                self.loaded_modules[module_name] = module_info
            except Exception as e:
                print(f"Warning: Could not load module '{module_name}': {e}")
        else:
            print(
                f"Warning: Module file '{module_file}' not found for module '{module_name}'"
            )


class TruthTableGenerator:
    """Generates and displays truth tables for combinational logic."""

    def __init__(self, evaluator: LogicEvaluator):
        self.evaluator = evaluator

    def generate_truth_table(self, max_combinations: int = 256) -> List[Dict[str, int]]:
        """
        Generate truth table for all input combinations.

        Args:
            max_combinations: Maximum number of input combinations to test

        Returns:
            List of dictionaries containing input and output values for each combination
        """
        inputs = self.evaluator.inputs
        bus_info = self.evaluator.bus_info

        # Calculate total number of input bits
        total_input_bits = 0
        for input_name in inputs:
            if input_name in bus_info:
                total_input_bits += bus_info[input_name]["width"]
            else:
                total_input_bits += 1

        # Limit combinations if too many inputs
        total_combinations = 2**total_input_bits
        if total_combinations > max_combinations:
            print(
                f"Warning: Too many input combinations ({total_combinations}). "
                f"Limiting to first {max_combinations} combinations."
            )

        truth_table = []
        combinations_to_test = min(total_combinations, max_combinations)

        for i in range(combinations_to_test):
            # Convert index to bus values
            input_values = {}
            bit_offset = 0

            for input_name in inputs:
                if input_name in bus_info:
                    width = bus_info[input_name]["width"]
                    # Extract bits for this bus from the combination index
                    bus_value = (i >> (total_input_bits - bit_offset - width)) & (
                        (1 << width) - 1
                    )
                    input_values[input_name] = bus_value
                    bit_offset += width
                else:
                    # Single bit
                    bit_value = (i >> (total_input_bits - bit_offset - 1)) & 1
                    input_values[input_name] = bit_value
                    bit_offset += 1

            # Evaluate outputs
            output_values = self.evaluator.evaluate(input_values)

            # Combine inputs and outputs
            row = {**input_values, **output_values}
            truth_table.append(row)

        return truth_table

    def print_truth_table(self, truth_table: List[Dict[str, int]]):
        """Print a formatted truth table with proper bus formatting."""
        if not truth_table:
            print("No truth table data to display.")
            return

        inputs = self.evaluator.inputs
        outputs = self.evaluator.outputs
        bus_info = self.evaluator.bus_info

        # Create headers with bus information
        input_headers = []
        output_headers = []

        for inp in inputs:
            if inp in bus_info and bus_info[inp]["width"] > 1:
                width = bus_info[inp]["width"]
                msb, lsb = bus_info[inp]["msb"], bus_info[inp]["lsb"]
                input_headers.append(f"{inp}[{msb}:{lsb}]")
            else:
                input_headers.append(inp)

        for out in outputs:
            if out in bus_info and bus_info[out]["width"] > 1:
                width = bus_info[out]["width"]
                msb, lsb = bus_info[out]["msb"], bus_info[out]["lsb"]
                output_headers.append(f"{out}[{msb}:{lsb}]")
            else:
                output_headers.append(out)

        # Print header
        header_inputs = " ".join(f"{header:>6}" for header in input_headers)
        header_outputs = " ".join(f"{header:>6}" for header in output_headers)
        print("Truth Table:")
        print(f"{header_inputs} | {header_outputs}")
        print("-" * (len(header_inputs) + 3 + len(header_outputs)))

        # Print data rows
        for row in truth_table:
            input_values = " ".join(f"{row[inp]:>6}" for inp in inputs)
            output_values = " ".join(f"{row[out]:>6}" for out in outputs)
            print(f"{input_values} | {output_values}")


class TestRunner:
    """Runs test cases from JSON files against the simulator."""

    def __init__(self, evaluator: LogicEvaluator):
        self.evaluator = evaluator

    def load_tests(self, test_file: str) -> List[Dict[str, Any]]:
        """Load test cases from a JSON file."""
        try:
            with open(test_file, "r", encoding="utf-8") as f:
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
            input_values = {k: v for k, v in test.items() if k != "expect"}
            expected_outputs = test.get("expect", {})

            # Run simulation
            actual_outputs = self.evaluator.evaluate(input_values)

            # Check results
            test_passed = True
            for output_name, expected_value in expected_outputs.items():
                if output_name not in actual_outputs:
                    print(f"Test {i} failed: Output '{output_name}' not found")
                    test_passed = False
                elif actual_outputs[output_name] != expected_value:
                    print(
                        f"Test {i} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value}"
                    )
                    test_passed = False

            if test_passed:
                print(f"Test {i} passed")
                passed += 1

        return passed, total


def main():
    global gargs
    """Main function to run the SystemVerilog simulator."""
    parser = argparse.ArgumentParser(
        description="SystemVerilog Simulator for Game Development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--file", required=True, help="SystemVerilog file to simulate")
    parser.add_argument("--test", help="JSON test file (optional)")
    parser.add_argument(
        "--max-combinations",
        type=int,
        default=256,
        help="Maximum number of input combinations to test (default: 256)",
    )

    args = parser.parse_args()
    gargs = args

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
            module_info["inputs"],
            module_info["outputs"],
            module_info["assignments"],
            module_info.get("instantiations", []),
            module_info.get("bus_info", {}),
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
                print("All tests passed!")
            else:
                print(f"{total - passed} test(s) failed.")
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


gargs = None
if __name__ == "__main__":
    main()
