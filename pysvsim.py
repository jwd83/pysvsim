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
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


# Global module cache to prevent repeated parsing of the same modules
GLOBAL_MODULE_CACHE = {}


def clear_module_cache():
    """Clear the global module cache. Useful for testing or when modules change."""
    global GLOBAL_MODULE_CACHE
    GLOBAL_MODULE_CACHE.clear()


class SystemVerilogParser:
    """Parser for a subset of SystemVerilog focused on basic combinational logic."""

    def __init__(self):
        self.module_name = ""
        self.inputs = []
        self.outputs = []
        self.wires = []
        self.bus_info = {}  # Track bus widths and ranges
        self.assignments = {}
        self.slice_assignments = (
            []
        )  # Track bus slice assignments like out[31:24] = in[7:0]
        self.concat_assignments = (
            []
        )  # Track concatenation assignments like {w, x, y, z} = expr
        self.instantiations = []
        self.sequential_blocks = []  # Track always_ff blocks and other sequential logic
        self.clock_signals = set()  # Track identified clock signals
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
        
        # Parse sequential logic blocks
        self._parse_sequential_blocks(content)

        return {
            "name": self.module_name,
            "inputs": self.inputs.copy(),
            "outputs": self.outputs.copy(),
            "assignments": self.assignments.copy(),
            "slice_assignments": self.slice_assignments.copy(),
            "concat_assignments": self.concat_assignments.copy(),
            "instantiations": self.instantiations.copy(),
            "sequential_blocks": self.sequential_blocks.copy(),
            "clock_signals": list(self.clock_signals),
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
        tokens = re.findall(
            r"\b(?:input|output|wire|logic)\b|\[[^\]]+\]|\w+|,", port_list
        )

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
        """Parse wire declarations, including bus wires and initialized wires."""
        # Handle bus wire declarations with initialization like: wire [24:0] v1 = expression;
        bus_wire_init_pattern = r"wire\s+\[(\d+):(\d+)\]\s+(\w+)\s*=\s*([^;]+)\s*;"
        bus_wire_init_declarations = re.findall(bus_wire_init_pattern, content)

        for msb, lsb, wire_name, expression in bus_wire_init_declarations:
            msb, lsb = int(msb), int(lsb)
            width = abs(msb - lsb) + 1
            self.bus_info[wire_name] = {"msb": msb, "lsb": lsb, "width": width}
            self.wires.append(wire_name)
            # Treat the initialization as an assignment
            self.assignments[wire_name] = expression.strip()

        # Handle single-bit wire declarations with initialization like: wire temp = expression;
        single_wire_init_pattern = r"wire\s+(\w+)\s*=\s*([^;]+)\s*;"
        single_wire_init_declarations = re.findall(single_wire_init_pattern, content)

        for wire_name, expression in single_wire_init_declarations:
            if wire_name not in self.bus_info:
                self.bus_info[wire_name] = {"msb": 0, "lsb": 0, "width": 1}
                self.wires.append(wire_name)
                # Treat the initialization as an assignment
                self.assignments[wire_name] = expression.strip()

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
        # Enhanced pattern to capture all assignment types including concatenation targets
        assign_pattern = r"assign\s+([^=]+)\s*=\s*([^;]+)\s*;"
        assignments = re.findall(assign_pattern, content)

        for output_signal, expression in assignments:
            # Clean up both output_signal and expression
            output_signal = output_signal.strip()
            expression = expression.strip()

            # Check if this is a concatenation assignment like {w, x, y, z} = expr
            if output_signal.startswith("{") and output_signal.endswith("}"):
                # Parse concatenation target
                targets = output_signal[1:-1].strip()  # Remove braces
                target_list = [t.strip() for t in targets.split(",")]
                self.concat_assignments.append(
                    {"targets": target_list, "expression": expression}
                )
            # Check if this is a bus slice assignment like out[31:24] = in[7:0]
            else:
                slice_match = re.match(r"(\w+)\[(\d+):(\d+)\]", output_signal)
                if slice_match:
                    # This is a bus slice assignment
                    signal_name = slice_match.group(1)
                    msb = int(slice_match.group(2))
                    lsb = int(slice_match.group(3))
                    self.slice_assignments.append(
                        {
                            "signal": signal_name,
                            "msb": msb,
                            "lsb": lsb,
                            "expression": expression,
                        }
                    )
                else:
                    # Regular assignment
                    base_signal_match = re.match(
                        r"(\w+)(?:\[\d+:\d+\])?", output_signal
                    )
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
            # Pattern to match .port_name(signal_name) connections including bit selections like A[0], bus slices like A[3:0], and literals like 1'b0
            conn_pattern = r"\.([\w]+)\(([\w\[\]:']+)\)"
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
    
    def _parse_sequential_blocks(self, content: str):
        """Parse sequential logic blocks like always_ff."""
        # Find all always_ff blocks with proper begin/end matching
        always_ff_starts = list(re.finditer(r'always_ff\s*@\s*\(([^)]+)\)\s*begin', content))
        
        for start_match in always_ff_starts:
            sensitivity_list = start_match.group(1).strip()
            
            # Find matching end by counting nested begin/end pairs
            start_pos = start_match.end() - 5  # Position of 'begin'
            begin_count = 1
            pos = start_match.end()
            block_end_pos = None
            
            while pos < len(content) and begin_count > 0:
                # Look for next 'begin' or 'end'
                begin_match = re.search(r'\bbegin\b', content[pos:])
                end_match = re.search(r'\bend\b', content[pos:])
                
                next_begin_pos = (pos + begin_match.start()) if begin_match else float('inf')
                next_end_pos = (pos + end_match.start()) if end_match else float('inf')
                
                if next_begin_pos < next_end_pos:
                    # Found another 'begin'
                    begin_count += 1
                    pos = next_begin_pos + 5
                elif next_end_pos != float('inf'):
                    # Found an 'end'
                    begin_count -= 1
                    if begin_count == 0:
                        block_end_pos = next_end_pos
                        break
                    pos = next_end_pos + 3
                else:
                    # No more begin/end found
                    break
            
            if block_end_pos is not None:
                # Extract the block content between the outer begin/end
                block_content = content[start_match.end():block_end_pos].strip()
                
                # Parse sensitivity list to find clock and edge type
                clock_info = self._parse_sensitivity_list(sensitivity_list)
                
                # Parse assignments within the block
                assignments = self._parse_sequential_assignments(block_content)
                
                sequential_block = {
                    'type': 'always_ff',
                    'clock': clock_info['clock'],
                    'edge': clock_info['edge'],
                    'assignments': assignments
                }
                
                self.sequential_blocks.append(sequential_block)
                self.clock_signals.add(clock_info['clock'])
    
    def _parse_sensitivity_list(self, sensitivity_list: str) -> Dict[str, str]:
        """Parse sensitivity list like 'posedge clk' or 'negedge reset'."""
        sensitivity_list = sensitivity_list.strip()
        
        if sensitivity_list.startswith('posedge'):
            clock_name = sensitivity_list.replace('posedge', '').strip()
            return {'clock': clock_name, 'edge': 'posedge'}
        elif sensitivity_list.startswith('negedge'):
            clock_name = sensitivity_list.replace('negedge', '').strip()
            return {'clock': clock_name, 'edge': 'negedge'}
        else:
            # Default to posedge for unspecified edge
            return {'clock': sensitivity_list, 'edge': 'posedge'}
    
    def _parse_sequential_assignments(self, block_content: str) -> List[Dict[str, str]]:
        """Parse assignments within a sequential block."""
        assignments = []
        
        # Clean the content by removing begin/end statements and normalizing whitespace
        clean_content = block_content
        clean_content = re.sub(r'\s*begin\s*', ' ', clean_content)
        clean_content = re.sub(r'\s*end\s*', ' ', clean_content)
        clean_content = ' '.join(clean_content.split())  # Normalize whitespace
        
        # Use a more sophisticated approach to parse if-else chains
        # Look for if statements with nested structure
        if_match = re.search(r'if\s*\(([^)]+)\)(.+?)(?=else|$)', clean_content)
        if if_match:
            # Parse if condition and body
            if_condition = if_match.group(1).strip()
            if_body = if_match.group(2).strip()
            
            # Look for assignment in if body
            if_assign_match = re.search(r'(\w+)\s*<=\s*([^;]+)', if_body)
            if if_assign_match:
                assignments.append({
                    'type': 'conditional_assignment',
                    'condition': if_condition,
                    'target': if_assign_match.group(1),
                    'expression': if_assign_match.group(2).strip()
                })
        
        # Look for else if statements
        else_if_matches = re.finditer(r'else\s+if\s*\(([^)]+)\)(.+?)(?=else|$)', clean_content)
        for else_if_match in else_if_matches:
            elif_condition = else_if_match.group(1).strip()
            elif_body = else_if_match.group(2).strip()
            
            # Look for assignment in else if body
            elif_assign_match = re.search(r'(\w+)\s*<=\s*([^;]+)', elif_body)
            if elif_assign_match:
                assignments.append({
                    'type': 'conditional_assignment',
                    'condition': elif_condition,
                    'target': elif_assign_match.group(1),
                    'expression': elif_assign_match.group(2).strip()
                })
        
        # Look for plain else statements (no additional condition)
        else_match = re.search(r'else(?!\s+if)\s*(.+?)$', clean_content)
        if else_match:
            else_body = else_match.group(1).strip()
            
            # Look for assignment in else body
            else_assign_match = re.search(r'(\w+)\s*<=\s*([^;]+)', else_body)
            if else_assign_match:
                assignments.append({
                    'type': 'conditional_assignment',
                    'condition': '!(previous_conditions)',  # Placeholder - will be handled by evaluator
                    'target': else_assign_match.group(1),
                    'expression': else_assign_match.group(2).strip()
                })
        
        return assignments
    
    def _parse_if_statement(self, statement: str) -> Optional[Dict[str, Any]]:
        """Parse if statements within sequential blocks."""
        # Handle simple if-else structure: if (condition) target <= expression
        if_pattern = r'if\s*\(([^)]+)\)\s*begin?\s*(\w+)\s*<=\s*([^;]+)'
        match = re.match(if_pattern, statement)
        
        if match:
            condition = match.group(1).strip()
            target = match.group(2).strip()
            expression = match.group(3).strip()
            
            return {
                'type': 'conditional_assignment',
                'condition': condition,
                'target': target,
                'expression': expression
            }
        
        return None
    
    def _parse_complex_if_statement(self, statement: str) -> List[Dict[str, Any]]:
        """Parse complex if/else if statements like those in counter."""
        assignments = []
        
        # Handle patterns like "if (count == 0) count <= 1"
        if_pattern = r'if\s*\(([^)]+)\)\s*(\w+)\s*<=\s*([^;\s]+)'
        elif_pattern = r'else\s+if\s*\(([^)]+)\)\s*(\w+)\s*<=\s*([^;\s]+)'
        else_pattern = r'else\s+(\w+)\s*<=\s*([^;\s]+)'
        
        # Try to match if statement
        if_match = re.search(if_pattern, statement)
        if if_match:
            condition = if_match.group(1).strip()
            target = if_match.group(2).strip()
            expression = if_match.group(3).strip()
            
            assignments.append({
                'type': 'conditional_assignment',
                'condition': condition,
                'target': target,
                'expression': expression
            })
        
        # Try to find all else if statements
        elif_matches = re.finditer(elif_pattern, statement)
        for elif_match in elif_matches:
            condition = elif_match.group(1).strip()
            target = elif_match.group(2).strip()
            expression = elif_match.group(3).strip()
            
            assignments.append({
                'type': 'conditional_assignment',
                'condition': condition,
                'target': target,
                'expression': expression
            })
        
        # Try to find else statement
        else_match = re.search(else_pattern, statement)
        if else_match:
            target = else_match.group(1).strip()
            expression = else_match.group(2).strip()
            
            # Else is treated as "if (1)" - always true condition
            assignments.append({
                'type': 'conditional_assignment',
                'condition': '1',  # Always true
                'target': target,
                'expression': expression
            })
        
        return assignments


class LogicEvaluator:
    """Evaluates SystemVerilog expressions with given input values."""

    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        assignments: Dict[str, str],
        instantiations: List[Dict[str, Any]] = None,
        bus_info: Dict[str, Dict] = None,
        slice_assignments: List[Dict[str, Any]] = None,
        concat_assignments: List[Dict[str, Any]] = None,
        current_file_path: str = None,
    ):
        self.inputs = inputs
        self.outputs = outputs
        self.assignments = assignments
        self.slice_assignments = slice_assignments or []
        self.concat_assignments = concat_assignments or []
        self.instantiations = instantiations or []
        self.bus_info = bus_info or {}
        self.current_file_path = current_file_path

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
                    new_value = self._evaluate_expression(
                        expression, signal_values, signal_name
                    )
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

        # Process slice assignments after regular assignments
        for slice_assign in self.slice_assignments:
            signal_name = slice_assign["signal"]
            msb = slice_assign["msb"]
            lsb = slice_assign["lsb"]
            expression = slice_assign["expression"]

            # Evaluate the slice expression - determine the target width for the expression
            expr_width = width = abs(msb - lsb) + 1
            slice_value = self._evaluate_expression(expression, signal_values)
            # Mask to the expected width
            mask_expr = (1 << expr_width) - 1
            slice_value = slice_value & mask_expr

            # Initialize the target signal if it doesn't exist
            if signal_name not in signal_values:
                signal_values[signal_name] = 0

            # Update the specific slice of the bus
            width = abs(msb - lsb) + 1
            shift = lsb if msb >= lsb else msb
            mask = (1 << width) - 1

            # Clear the target bits and set the new value
            signal_values[signal_name] = (
                signal_values[signal_name] & ~(mask << shift)
            ) | ((slice_value & mask) << shift)

            # Also expand this updated bus to individual bits for consistency
            if signal_name in self.bus_info and self.bus_info[signal_name]["width"] > 1:
                self._expand_bus_to_bits(
                    signal_name, signal_values[signal_name], signal_values
                )

        # Process concatenation assignments after slice assignments
        for concat_assign in self.concat_assignments:
            targets = concat_assign["targets"]
            expression = concat_assign["expression"]

            # Evaluate the expression to get the combined value
            combined_value = self._evaluate_expression(expression, signal_values)

            # Calculate total width needed for all targets
            total_width = 0
            target_widths = []
            for target in targets:
                if target in self.bus_info:
                    width = self.bus_info[target]["width"]
                else:
                    width = 1  # Default to single bit
                target_widths.append(width)
                total_width += width

            # Split the combined value across targets (MSB first)
            current_value = combined_value
            for i, target in enumerate(
                reversed(targets)
            ):  # Process in reverse order (LSB first)
                width = target_widths[len(targets) - 1 - i]
                mask = (1 << width) - 1
                target_value = current_value & mask
                current_value >>= width

                signal_values[target] = target_value

                # Also expand this bus to individual bits for consistency
                if target in self.bus_info and self.bus_info[target]["width"] > 1:
                    self._expand_bus_to_bits(target, target_value, signal_values)

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
        self, expression: str, signal_values: Dict[str, int], target_signal: str = None
    ) -> int:
        """Evaluate a single SystemVerilog expression."""
        # Replace signal names with their values
        eval_expr = expression.strip()

        # Handle simple bus-to-bus assignment (like Y = A)
        if eval_expr in signal_values:
            return signal_values[eval_expr]

        # Handle concatenation expressions like {a, b, c}
        if eval_expr.startswith("{") and eval_expr.endswith("}"):
            return self._evaluate_concatenation(eval_expr, signal_values)

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
            result = int(result)

            # Apply bit masking based on target signal width or expression content
            if target_signal and target_signal in self.bus_info:
                bus_info = self.bus_info[target_signal]
                if bus_info["width"] > 1:
                    # Multi-bit signal - mask to the appropriate width
                    width = bus_info["width"]
                    mask = (1 << width) - 1
                    return result & mask

            # Check if the original expression was a bus slice (like in[7:0])
            if re.match(r"\w+\[\d+:\d+\]", expression.strip()):
                # This is a bus slice expression - don't force to single bit
                return result

            # Check if the original expression contains a bus slice (like ~b[2:0])
            if re.search(r"\w+\[\d+:\d+\]", expression.strip()):
                # Expression contains bus slice - don't force to single bit
                return result

            # Default to single bit for unknown signals or single-bit signals
            return result & 1
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

    def _evaluate_concatenation(
        self, concat_expr: str, signal_values: Dict[str, int]
    ) -> int:
        """Evaluate concatenation expressions like {a, b, c} and replication like {N{expr}}."""
        # Remove curly braces
        inner_expr = concat_expr[1:-1].strip()

        # Split by comma and evaluate each part
        parts = [part.strip() for part in inner_expr.split(",")]

        result = 0
        for part in parts:
            part_width = 1  # Default width
            replication_match = None  # Initialize for each part

            # Check if this part is itself a concatenation (nested braces)
            if part.startswith("{") and part.endswith("}"):
                # Recursively evaluate nested concatenation
                part_value = self._evaluate_concatenation(part, signal_values)
                # For nested concatenations, we need to calculate the actual width
                # by analyzing the inner content
                part_width = self._calculate_concatenation_width(part, signal_values)

            # Check for replication pattern like {N{expression}}
            elif replication_match := re.match(r"(\d+)\{(.+?)\}", part):
                # Handle replication: N{expression}
                count = int(replication_match.group(1))
                expr = replication_match.group(2).strip()

                # Evaluate the replicated expression
                replicated_value = self._evaluate_expression(expr, signal_values)

                # Determine the width of the replicated expression
                # For single bit expressions, width is 1
                expr_width = 1  # Default for single bits like in[7]
                if expr in self.bus_info:
                    expr_width = self.bus_info[expr]["width"]
                elif re.match(r"\w+\[\d+:\d+\]", expr):
                    # Handle bus slice width calculation
                    slice_match = re.match(r"\w+\[(\d+):(\d+)\]", expr)
                    if slice_match:
                        msb, lsb = int(slice_match.group(1)), int(slice_match.group(2))
                        expr_width = abs(msb - lsb) + 1

                # Create the replicated bits
                part_value = 0
                for i in range(count):
                    part_value = (part_value << expr_width) | (
                        replicated_value & ((1 << expr_width) - 1)
                    )

                part_width = count * expr_width

            # Evaluate each part of the concatenation
            elif part in signal_values:
                part_value = signal_values[part]
            else:
                # Handle literal constants like 2'b11, 4'hF, 8'd255
                literal_match = re.match(r"(\d+)'([bhdBHD])([0-9a-fA-F]+)", part)
                if literal_match:
                    width = int(literal_match.group(1))
                    base = literal_match.group(2).lower()
                    value_str = literal_match.group(3)

                    if base == "b":  # Binary
                        part_value = int(value_str, 2)
                    elif base == "h":  # Hexadecimal
                        part_value = int(value_str, 16)
                    elif base == "d":  # Decimal
                        part_value = int(value_str, 10)
                    else:
                        part_value = 0

                    # Mask to specified width
                    part_value &= (1 << width) - 1
                # Handle bit selections like in[0], in[1], etc.
                else:
                    bit_select_match = re.match(r"(\w+)\[(\d+)\]", part)
                    if bit_select_match:
                        bus_name = bit_select_match.group(1)
                        bit_index = int(bit_select_match.group(2))
                        bit_signal = f"{bus_name}[{bit_index}]"
                        if bit_signal in signal_values:
                            part_value = signal_values[bit_signal]
                        else:
                            # Extract from bus value
                            if bus_name in signal_values:
                                bus_value = signal_values[bus_name]
                                part_value = (bus_value >> bit_index) & 1
                            else:
                                part_value = 0
                    else:
                        part_value = 0

            # Determine the width of this part (if not already set by replication logic)
            if not replication_match:
                if part in signal_values and part in self.bus_info:
                    part_width = self.bus_info[part]["width"]
                elif re.match(r"(\d+)'[bhdBHD]", part):  # Literal constant
                    literal_match = re.match(r"(\d+)'[bhdBHD]", part)
                    part_width = int(literal_match.group(1))
                # part_width already defaults to 1

            # Shift previous results and add this part (MSB first)
            result = (result << part_width) | (part_value & ((1 << part_width) - 1))

        return result

    def _calculate_concatenation_width(
        self, concat_expr: str, signal_values: Dict[str, int]
    ) -> int:
        """Calculate the total bit width of a concatenation expression."""
        # Remove curly braces
        inner_expr = concat_expr[1:-1].strip()

        # Split by comma and calculate width of each part
        parts = [part.strip() for part in inner_expr.split(",")]

        total_width = 0
        for part in parts:
            # Check for replication pattern like {N{expression}}
            replication_match = re.match(r"(\d+)\{(.+?)\}", part)
            if replication_match:
                count = int(replication_match.group(1))
                expr = replication_match.group(2).strip()

                # Determine width of replicated expression
                expr_width = 1  # Default for single bits like in[7]
                if expr in self.bus_info:
                    expr_width = self.bus_info[expr]["width"]
                elif re.match(r"\w+\[\d+:\d+\]", expr):
                    slice_match = re.match(r"\w+\[(\d+):(\d+)\]", expr)
                    if slice_match:
                        msb, lsb = int(slice_match.group(1)), int(slice_match.group(2))
                        expr_width = abs(msb - lsb) + 1

                total_width += count * expr_width

            elif part in signal_values and part in self.bus_info:
                total_width += self.bus_info[part]["width"]
            elif re.match(r"(\d+)'[bhdBHD]", part):  # Literal constant
                literal_match = re.match(r"(\d+)'[bhdBHD]", part)
                total_width += int(literal_match.group(1))
            else:
                total_width += 1  # Default single bit

        return total_width

    def _evaluate_instantiation(
        self, inst: Dict[str, Any], signal_values: Dict[str, int]
    ):
        """Evaluate a module instantiation."""
        module_type = inst["module_type"]
        connections = inst["connections"]
        instance_name = inst.get("instance_name", "unknown")

        # Load the referenced module if not already loaded
        if module_type not in GLOBAL_MODULE_CACHE:
            self._load_module(module_type)
        # else:
        #     print(f"Using cached module '{module_type}'")

        if module_type not in GLOBAL_MODULE_CACHE:
            raise ValueError(f"Could not load module '{module_type}' for instance '{instance_name}'")

        module_info = GLOBAL_MODULE_CACHE[module_type]

        # Build input values for the instantiated module
        inst_input_values = {}
        for port_name, signal_name in connections.items():
            if port_name in module_info["inputs"]:
                signal_value = None

                # Handle SystemVerilog literals like 1'b0, 1'b1
                if re.match(r"\d+'b[01]+", signal_name):
                    # Parse SystemVerilog binary literal
                    literal_match = re.match(r"(\d+)'b([01]+)", signal_name)
                    if literal_match:
                        width = int(literal_match.group(1))
                        binary_value = literal_match.group(2)
                        signal_value = int(binary_value, 2)
                # Handle direct signal reference
                elif signal_name in signal_values:
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
                    available_signals = list(signal_values.keys())
                    raise ValueError(
                        f"Signal '{signal_name}' not found for instantiation '{instance_name}' (port '{port_name}'). Available signals: {available_signals[:10]}{'...' if len(available_signals) > 10 else ''}"
                    )

        # Create evaluator for the instantiated module
        inst_evaluator = LogicEvaluator(
            module_info["inputs"],
            module_info["outputs"],
            module_info["assignments"],
            module_info.get("instantiations", []),
            module_info.get("bus_info", {}),
            module_info.get("slice_assignments", []),
            module_info.get("concat_assignments", []),
            self.current_file_path,
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
                    signal_values[bus_name] = (
                        signal_values[bus_name] & ~(mask << shift)
                    ) | ((output_value & mask) << shift)

                    # Also expand this updated bus to individual bits for consistency
                    if (
                        bus_name in self.bus_info
                        and self.bus_info[bus_name]["width"] > 1
                    ):
                        self._expand_bus_to_bits(
                            bus_name, signal_values[bus_name], signal_values
                        )
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

    def count_nand_gates(self) -> int:
        """Count the total number of NAND gates in the module hierarchy."""
        return self._count_nand_gates_recursive("top_module", set())

    def _count_nand_gates_recursive(self, module_name: str, visited: set) -> int:
        """Recursively count NAND gates in a module and its sub-modules."""
        # Avoid infinite recursion
        if module_name in visited:
            return 0
        visited.add(module_name)

        # Check if this is the primitive NAND gate
        if module_name == "nand_gate":
            return 1

        # Load module if not already loaded
        if module_name not in GLOBAL_MODULE_CACHE:
            # For the top module, use current module info
            if module_name == "top_module":
                # Create a temporary module info from current evaluator
                temp_module_info = {
                    "name": "top_module",
                    "instantiations": self.instantiations,
                }
                GLOBAL_MODULE_CACHE[module_name] = temp_module_info
            else:
                self._load_module(module_name)

        if module_name not in GLOBAL_MODULE_CACHE:
            return 0

        module_info = GLOBAL_MODULE_CACHE[module_name]
        total_nands = 0

        # Count NAND gates in all instantiated sub-modules
        for inst in module_info.get("instantiations", []):
            sub_module_type = inst["module_type"]
            sub_nands = self._count_nand_gates_recursive(
                sub_module_type, visited.copy()
            )
            total_nands += sub_nands

        return total_nands

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
            if self.current_file_path:
                module_file = os.path.join(
                    os.path.dirname(self.current_file_path), f"{module_name}.sv"
                )
                if os.path.exists(module_file):
                    load_file = True
                    # print(f"Loading module '{module_name}' from {module_file}")
            elif hasattr(gargs, "file") and gargs.file:
                module_file = os.path.join(
                    os.path.dirname(gargs.file), f"{module_name}.sv"
                )
                if os.path.exists(module_file):
                    load_file = True
                    # print(f"Loading module '{module_name}' from {module_file}")
            # print(f"Looking for module '{module_name}' in {module_file}")
        if load_file:
            try:
                # print(f"Loading module '{module_name}' from disk: {module_file}")
                parser = SystemVerilogParser()
                module_info = parser.parse_file(module_file)
                GLOBAL_MODULE_CACHE[module_name] = module_info
            except Exception as e:
                print(f"Warning: Could not load module '{module_name}': {e}")
        else:
            print(
                f"Warning: Module file '{module_file}' not found for module '{module_name}'"
            )


class SequentialLogicEvaluator:
    """Evaluator for sequential (clocked) SystemVerilog modules."""
    
    def __init__(self, inputs: List[str], outputs: List[str], assignments: Dict[str, str],
                 instantiations: List[Dict], bus_info: Dict[str, Dict], 
                 slice_assignments: List[Dict], concat_assignments: List[Dict],
                 sequential_blocks: List[Dict], clock_signals: List[str], filepath: str = ""):
        
        # Initialize combinational evaluator for non-clocked logic
        self.comb_evaluator = LogicEvaluator(
            inputs, outputs, assignments, instantiations, bus_info,
            slice_assignments, concat_assignments, filepath
        )
        
        self.inputs = inputs
        self.outputs = outputs
        self.sequential_blocks = sequential_blocks
        self.clock_signals = set(clock_signals)
        self.state = {}  # Current state of sequential elements
        self.next_state = {}  # Next state to update on clock edge
        
        # Store bus_info for compatibility with TruthTableGenerator
        self.bus_info = bus_info
        
        # Initialize all outputs to 0
        for output in outputs:
            self.state[output] = 0
    
    def evaluate_cycle(self, input_values: Dict[str, int]) -> Dict[str, int]:
        """Evaluate one clock cycle with given inputs."""
        
        # First, evaluate combinational logic with current state + inputs
        current_signals = {**self.state, **input_values}
        
        # Get combinational outputs (handles instantiations, assigns, etc.)
        comb_outputs = self.comb_evaluator.evaluate(input_values)
        current_signals.update(comb_outputs)
        
        # Process sequential blocks to determine next state
        self.next_state = self.state.copy()
        
        for block in self.sequential_blocks:
            if block['type'] == 'always_ff':
                clock_signal = block['clock']
                
                # Check if clock signal changed (simulate clock edge)
                # For now, we'll assume every evaluation represents a clock edge
                self._evaluate_sequential_block(block, current_signals)
        
        # Update state (clock edge occurs)
        self.state.update(self.next_state)
        
        # Return current output values
        output_values = {}
        for output in self.outputs:
            output_values[output] = self.state.get(output, 0)
        
        return output_values
    
    def _evaluate_sequential_block(self, block: Dict, signals: Dict[str, int]):
        """Evaluate a sequential block and update next_state."""
        # Create enhanced signal context that includes current state for self-referencing expressions
        enhanced_signals = signals.copy()
        enhanced_signals.update(self.state)  # Include current state values
        
        for assignment in block['assignments']:
            if assignment['type'] == 'assignment':
                target = assignment['target']
                expression = assignment['expression']
                value = self.comb_evaluator._evaluate_expression(expression, enhanced_signals, target)
                self.next_state[target] = value
                # Update enhanced_signals so subsequent assignments see the new value
                enhanced_signals[target] = value
                
            elif assignment['type'] == 'conditional_assignment':
                condition = assignment['condition']
                target = assignment['target']
                expression = assignment['expression']
                
                # Evaluate condition with enhanced signal context
                condition_value = self.comb_evaluator._evaluate_expression(condition, enhanced_signals)
                if condition_value:
                    value = self.comb_evaluator._evaluate_expression(expression, enhanced_signals, target)
                    self.next_state[target] = value
                    # Update enhanced_signals so subsequent assignments see the new value
                    enhanced_signals[target] = value
    
    def reset_state(self):
        """Reset all sequential state to initial values."""
        self.state = {}
        self.next_state = {}
        for output in self.outputs:
            self.state[output] = 0
    
    def count_nand_gates(self) -> int:
        """Count NAND gates by delegating to the combinational evaluator."""
        return self.comb_evaluator.count_nand_gates()
    
    def evaluate(self, input_values: Dict[str, int]) -> Dict[str, int]:
        """Compatibility wrapper - evaluates one cycle for truth table generation."""
        return self.evaluate_cycle(input_values)


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


class TruthTableImageGenerator:
    """Generates truth table images for combinational logic."""
    
    def __init__(self, evaluator):
        self.evaluator = evaluator
    
    def generate_image(self, truth_table: List[Dict[str, int]], output_path: str):
        """Generate a PNG image of the truth table."""
        if not truth_table:
            return
        
        # Set up matplotlib for headless operation
        plt.switch_backend('Agg')
        
        inputs = self.evaluator.inputs
        outputs = self.evaluator.outputs
        bus_info = getattr(self.evaluator, 'bus_info', {})
        
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
        
        all_headers = input_headers + output_headers
        
        # Prepare data for table
        table_data = []
        for row in truth_table:
            row_data = []
            for inp in inputs:
                row_data.append(str(row[inp]))
            for out in outputs:
                row_data.append(str(row[out]))
            table_data.append(row_data)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(max(12, len(all_headers) * 1.5), max(8, len(table_data) * 0.4 + 2)))
        ax.axis('tight')
        ax.axis('off')
        
        # Create table
        table = ax.table(cellText=table_data,
                        colLabels=all_headers,
                        cellLoc='center',
                        loc='center')
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # Color the header
        for i in range(len(all_headers)):
            if i < len(input_headers):
                # Input columns in light blue
                table[(0, i)].set_facecolor('#E3F2FD')
            else:
                # Output columns in light green
                table[(0, i)].set_facecolor('#E8F5E8')
            table[(0, i)].set_text_props(weight='bold')
        
        # Color coding provides visual separation between inputs and outputs
        
        plt.title(f'Truth Table - {Path(output_path).stem}', fontsize=14, weight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()


class WaveformImageGenerator:
    """Generates professional waveform images for sequential logic."""
    
    def __init__(self, evaluator):
        self.evaluator = evaluator
    
    def generate_image(self, test_results: List[Dict], output_path: str):
        """Generate a professional PNG waveform image from test results."""
        if not test_results:
            return
        
        # Set up matplotlib for headless operation
        plt.switch_backend('Agg')
        
        # Extract and organize signals
        clock_signals = set()
        input_signals = set()
        output_signals = set()
        
        for result in test_results:
            if 'inputs' in result:
                for signal in result['inputs'].keys():
                    if 'clk' in signal.lower() or 'clock' in signal.lower():
                        clock_signals.add(signal)
                    else:
                        input_signals.add(signal)
            if 'outputs' in result:
                output_signals.update(result['outputs'].keys())
        
        # Order signals: clock first, then inputs, then outputs
        signals = (sorted(clock_signals) + 
                  sorted(input_signals) + 
                  sorted(output_signals))
        
        num_signals = len(signals)
        num_cycles = len(test_results)
        
        # Create figure with professional proportions
        fig_width = max(14, num_cycles * 1.5 + 2)
        fig_height = max(8, num_signals * 0.8 + 3)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # Professional color scheme
        clock_color = '#E74C3C'    # Red for clock - most important
        input_color = '#3498DB'    # Blue for inputs
        output_color = '#27AE60'   # Green for outputs
        grid_color = '#BDC3C7'     # Light gray for grid
        
        # Draw background grid for better readability
        for cycle in range(num_cycles + 1):
            ax.axvline(x=cycle, color=grid_color, alpha=0.4, linewidth=0.8, zorder=0)
        
        for i in range(num_signals):
            y = num_signals - i - 1
            ax.axhline(y=y + 0.9, color=grid_color, alpha=0.2, linewidth=0.5, zorder=0)
        
        # Generate professional waveforms
        for i, signal in enumerate(signals):
            y_base = num_signals - i - 1
            
            # Determine signal color
            if signal in clock_signals:
                color = clock_color
            elif signal in input_signals:
                color = input_color
            else:
                color = output_color
            
            # Extract values for this signal
            values = []
            for result in test_results:
                if signal in result.get('inputs', {}):
                    values.append(result['inputs'][signal])
                elif signal in result.get('outputs', {}):
                    values.append(result['outputs'][signal])
                else:
                    values.append(0)
            
            # Check if this is a multi-bit signal
            max_value = max(values) if values else 0
            is_multibit = max_value > 1
            
            # Special handling for clock signals
            if signal in clock_signals:
                self._draw_clock_waveform(ax, values, y_base, color, num_cycles)
            elif is_multibit:
                self._draw_multibit_waveform(ax, values, y_base, color, signal, num_cycles)
            else:
                self._draw_digital_waveform(ax, values, y_base, color, num_cycles)
        
        # Professional layout and styling
        ax.set_xlim(-0.1, num_cycles + 0.1)
        ax.set_ylim(-0.2, num_signals + 0.2)
        
        # Signal labels with clear typography and color coding
        ax.set_yticks([num_signals - i - 1 + 0.45 for i in range(num_signals)])
        signal_labels = []
        for signal in signals:
            if signal in clock_signals:
                signal_labels.append(f'{signal} (clk)')
            elif signal in input_signals:
                signal_labels.append(f'{signal} (in)')
            else:
                signal_labels.append(f'{signal} (out)')
        
        ax.set_yticklabels(signal_labels, fontsize=11, fontweight='bold')
        
        # Professional time axis
        ax.set_xticks([i + 0.5 for i in range(num_cycles)])
        ax.set_xticklabels([f'{i}' for i in range(num_cycles)], fontsize=11)
        
        # Clean professional styling
        ax.set_xlabel('Clock Cycle', fontsize=13, fontweight='bold', color='#2C3E50')
        ax.set_ylabel('Signals', fontsize=13, fontweight='bold', color='#2C3E50')
        
        # Remove all spines for ultra-clean look
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Professional title
        plt.title(f'Digital Waveform - {Path(output_path).stem}', 
                 fontsize=16, fontweight='bold', color='#2C3E50', pad=25)
        
        # Add subtle background
        ax.set_facecolor('#FAFAFA')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=200, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
    
    def _draw_clock_waveform(self, ax, values, y_base, color, num_cycles):
        """Draw a special clock waveform with clean square waves."""
        y_low = y_base + 0.15
        y_high = y_base + 0.75
        
        # Clock signals should show clean transitions
        for cycle in range(num_cycles):
            x_start = cycle
            x_end = cycle + 1
            x_mid = cycle + 0.5
            
            # Draw rising edge at start of cycle
            ax.plot([x_start, x_start], [y_low, y_high], color=color, linewidth=3, solid_capstyle='butt')
            # Draw high period (first half)
            ax.plot([x_start, x_mid], [y_high, y_high], color=color, linewidth=3, solid_capstyle='butt')
            # Draw falling edge at middle
            ax.plot([x_mid, x_mid], [y_high, y_low], color=color, linewidth=3, solid_capstyle='butt')
            # Draw low period (second half)
            ax.plot([x_mid, x_end], [y_low, y_low], color=color, linewidth=3, solid_capstyle='butt')
    
    def _draw_digital_waveform(self, ax, values, y_base, color, num_cycles):
        """Draw a clean digital (0/1) waveform."""
        y_low = y_base + 0.15
        y_high = y_base + 0.75
        line_width = 2.8
        
        # Start with initial level
        prev_level = y_high if values[0] > 0 else y_low
        
        for cycle in range(num_cycles):
            value = values[cycle]
            x_start = cycle
            x_end = cycle + 1
            current_level = y_high if value > 0 else y_low
            
            # Draw transition at start of cycle if needed
            if cycle == 0 or (values[cycle-1] > 0) != (value > 0):
                if cycle > 0:
                    ax.plot([x_start, x_start], [prev_level, current_level], 
                           color=color, linewidth=line_width, solid_capstyle='butt')
            
            # Draw horizontal line for this cycle
            ax.plot([x_start, x_end], [current_level, current_level], 
                   color=color, linewidth=line_width, solid_capstyle='butt')
            
            prev_level = current_level
    
    def _draw_multibit_waveform(self, ax, values, y_base, color, signal_name, num_cycles):
        """Draw a professional multi-bit waveform with clear value annotations."""
        y_top = y_base + 0.75
        y_bottom = y_base + 0.15
        y_center = y_base + 0.45
        
        for cycle in range(num_cycles):
            value = values[cycle]
            x_start = cycle
            x_end = cycle + 1
            x_center = cycle + 0.5
            
            # Draw bus representation with angled transitions
            if cycle == 0 or values[cycle-1] != value:
                # Value change - draw transition
                if cycle > 0:
                    # Draw angled transition from previous value
                    transition_width = 0.1
                    ax.plot([x_start - transition_width, x_start], 
                           [y_top, y_top], color=color, linewidth=2.5)
                    ax.plot([x_start - transition_width, x_start], 
                           [y_bottom, y_bottom], color=color, linewidth=2.5)
                    # Angled connectors
                    ax.plot([x_start - transition_width, x_start], 
                           [y_top, y_bottom], color=color, linewidth=2.5)
                    ax.plot([x_start - transition_width, x_start], 
                           [y_bottom, y_top], color=color, linewidth=2.5)
            
            # Draw horizontal bus lines
            ax.plot([x_start, x_end], [y_top, y_top], color=color, linewidth=2.5)
            ax.plot([x_start, x_end], [y_bottom, y_bottom], color=color, linewidth=2.5)
            
            # Add clear value annotation
            if value < 16:  # Single hex digit or small decimal
                bbox_props = dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.9, edgecolor='white')
                fontsize = 10
            else:  # Larger values
                bbox_props = dict(boxstyle='round,pad=0.25', facecolor=color, alpha=0.9, edgecolor='white')
                fontsize = 9
            
            ax.text(x_center, y_center, str(value), ha='center', va='center',
                   fontsize=fontsize, fontweight='bold', color='white', bbox=bbox_props)


class TestRunner:
    """Runs test cases from JSON files against the simulator."""

    def __init__(self, evaluator: LogicEvaluator):
        self.evaluator = evaluator
        self.test_cycles = []  # Store test cycles for waveform generation

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

    def run_tests(self, tests) -> Tuple[int, int]:
        """
        Run all test cases and return pass/fail counts.
        Supports both combinational and sequential test formats.

        Args:
            tests: List of test case dictionaries or sequential test format dict

        Returns:
            Tuple of (passed_count, total_count)
        """
        # Check if this is the new sequential test format
        if isinstance(tests, dict) and (tests.get('sequential') or tests.get('test_cases')):
            return self._run_new_sequential_tests(tests)
        # Check if this is the old sequential test format
        elif isinstance(tests, dict) and tests.get('test_type') == 'sequential':
            return self._run_sequential_tests(tests)
        else:
            return self._run_combinational_tests(tests)
    
    def _run_combinational_tests(self, tests: List[Dict[str, Any]]) -> Tuple[int, int]:
        """Run combinational logic tests (original format)"""
        print("\nRunning combinational tests...")
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
    
    def _run_sequential_tests(self, test_data: Dict[str, Any]) -> Tuple[int, int]:
        """Run sequential logic tests (new format)"""
        print("\nRunning sequential tests...")
        test_cycles = test_data.get('test_cycles', [])
        passed = 0
        total = len(test_cycles)
        
        # Reset sequential state if available
        if hasattr(self.evaluator, 'reset_state'):
            self.evaluator.reset_state()
        
        # Clear previous test cycles
        self.test_cycles = []
        
        for i, cycle_test in enumerate(test_cycles):
            cycle_num = cycle_test.get('cycle', i)
            input_values = cycle_test.get('inputs', {})
            expected_outputs = cycle_test.get('expected_outputs', {})
            description = cycle_test.get('description', f'Cycle {cycle_num}')
            
            # Run one clock cycle
            if hasattr(self.evaluator, 'evaluate_cycle'):
                actual_outputs = self.evaluator.evaluate_cycle(input_values)
            else:
                # Fallback for combinational evaluator
                actual_outputs = self.evaluator.evaluate(input_values)
            
            # Store cycle data for waveform generation
            self.test_cycles.append({
                'cycle': cycle_num,
                'inputs': input_values.copy(),
                'outputs': actual_outputs.copy(),
                'description': description
            })
            
            # Check results
            test_passed = True
            for output_name, expected_value in expected_outputs.items():
                if output_name not in actual_outputs:
                    print(f"Cycle {cycle_num} failed: Output '{output_name}' not found - {description}")
                    test_passed = False
                elif actual_outputs[output_name] != expected_value:
                    print(
                        f"Cycle {cycle_num} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value} - {description}"
                    )
                    test_passed = False
            
            if test_passed:
                print(f"Cycle {cycle_num} passed - {description}")
                passed += 1
        
        return passed, total
    
    def _run_new_sequential_tests(self, test_data: Dict[str, Any]) -> Tuple[int, int]:
        """Run new sequential logic tests format"""
        print("\nRunning sequential tests...")
        test_cases = test_data.get('test_cases', [])
        passed = 0
        total = 0
        
        # Reset sequential state if available
        if hasattr(self.evaluator, 'reset_state'):
            self.evaluator.reset_state()
        
        # Clear previous test cycles
        self.test_cycles = []
        cycle_counter = 0
        
        for test_case in test_cases:
            name = test_case.get('name', 'Unnamed test')
            
            if 'sequence' in test_case:
                # Handle sequence tests
                sequence_passed = True
                for step in test_case['sequence']:
                    input_values = step.get('inputs', {})
                    expected_outputs = step.get('expected', {})
                    
                    # Run one clock cycle
                    if hasattr(self.evaluator, 'evaluate_cycle'):
                        actual_outputs = self.evaluator.evaluate_cycle(input_values)
                    else:
                        actual_outputs = self.evaluator.evaluate(input_values)
                    
                    # Store cycle data for waveform generation
                    self.test_cycles.append({
                        'cycle': cycle_counter,
                        'inputs': input_values.copy(),
                        'outputs': actual_outputs.copy(),
                        'description': f'{name} - Step {cycle_counter}'
                    })
                    cycle_counter += 1
                    
                    # Check results for this step
                    for output_name, expected_value in expected_outputs.items():
                        if output_name not in actual_outputs:
                            print(f"{name} failed: Output '{output_name}' not found")
                            sequence_passed = False
                        elif actual_outputs[output_name] != expected_value:
                            print(
                                f"{name} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value}"
                            )
                            sequence_passed = False
                
                if sequence_passed:
                    print(f"{name} passed")
                    passed += 1
                total += 1
            
            else:
                # Handle single test cases
                input_values = test_case.get('inputs', {})
                expected_outputs = test_case.get('expected', {})
                
                # Run one clock cycle
                if hasattr(self.evaluator, 'evaluate_cycle'):
                    actual_outputs = self.evaluator.evaluate_cycle(input_values)
                else:
                    actual_outputs = self.evaluator.evaluate(input_values)
                
                # Store cycle data for waveform generation
                self.test_cycles.append({
                    'cycle': cycle_counter,
                    'inputs': input_values.copy(),
                    'outputs': actual_outputs.copy(),
                    'description': name
                })
                cycle_counter += 1
                
                # Check results
                test_passed = True
                for output_name, expected_value in expected_outputs.items():
                    if output_name not in actual_outputs:
                        print(f"{name} failed: Output '{output_name}' not found")
                        test_passed = False
                    elif actual_outputs[output_name] != expected_value:
                        print(
                            f"{name} failed: {output_name} = {actual_outputs[output_name]}, expected {expected_value}"
                        )
                        test_passed = False
                
                if test_passed:
                    print(f"{name} passed")
                    passed += 1
                total += 1
        
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
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the global module cache before running",
    )

    args = parser.parse_args()
    gargs = args

    # Clear cache if requested
    if args.clear_cache:
        clear_module_cache()
        print("Global module cache cleared.")

    try:
        # Parse SystemVerilog file
        print(f"Parsing SystemVerilog file: {args.file}")
        sv_parser = SystemVerilogParser()
        module_info = sv_parser.parse_file(args.file)

        print(f"Module: {module_info['name']}")
        print(f"Inputs: {module_info['inputs']}")
        print(f"Outputs: {module_info['outputs']}")

        # Create evaluator (sequential or combinational based on module content)
        # Check for direct sequential blocks or clock signals in sub-modules
        is_sequential = module_info.get("sequential_blocks") or module_info.get("clock_signals")
        
        # Also check if any instantiated sub-modules are sequential
        if not is_sequential:
            for inst in module_info.get("instantiations", []):
                module_type = inst["module_type"]
                # Check for known sequential modules (like register_1bit)
                if "register" in module_type.lower() or "reg" in module_type.lower():
                    is_sequential = True
                    break
        
        if is_sequential:
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
                args.file,
            )
            print(f"Sequential blocks detected: {len(module_info.get('sequential_blocks', []))}")
            print(f"Clock signals: {list(module_info.get('clock_signals', []))}")
        else:
            # Combinational logic - use LogicEvaluator
            evaluator = LogicEvaluator(
                module_info["inputs"],
                module_info["outputs"],
                module_info["assignments"],
                module_info.get("instantiations", []),
                module_info.get("bus_info", {}),
                module_info.get("slice_assignments", []),
                module_info.get("concat_assignments", []),
                args.file,
            )

        # Count NAND gates
        nand_count = evaluator.count_nand_gates()
        print(f"\nNAND Gate Count: {nand_count}")

        # Generate and display truth table (only for combinational logic)
        is_sequential = hasattr(evaluator, 'evaluate_cycle')
        if not is_sequential:
            truth_table_gen = TruthTableGenerator(evaluator)
            truth_table = truth_table_gen.generate_truth_table(args.max_combinations)
            truth_table_gen.print_truth_table(truth_table)
            
            # Generate truth table image
            image_path = str(Path(args.file).with_suffix('.png'))
            image_gen = TruthTableImageGenerator(evaluator)
            image_gen.generate_image(truth_table, image_path)
            print(f"\nTruth Table Image: {image_path}")
        else:
            print("\nTruth Table: Skipped (sequential logic module)")

        # Run tests if provided
        if args.test:
            test_runner = TestRunner(evaluator)
            tests = test_runner.load_tests(args.test)
            passed, total = test_runner.run_tests(tests)

            print(f"\nTest Results: {passed}/{total} passed")
            
            # Generate waveform image for sequential logic
            if is_sequential and test_runner.test_cycles:
                image_path = str(Path(args.file).with_suffix('.png'))
                waveform_gen = WaveformImageGenerator(evaluator)
                waveform_gen.generate_image(test_runner.test_cycles, image_path)
                print(f"Waveform Image: {image_path}")
            
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
