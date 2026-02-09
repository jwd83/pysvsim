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
import os
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


def parse_sv_range(range_expr: str) -> Tuple[int, int, int]:
    """Parse a SystemVerilog range expression like [7:0]."""
    range_match = re.match(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]$", range_expr.strip())
    if not range_match:
        raise ValueError(f"Invalid range expression: {range_expr}")
    msb = int(range_match.group(1))
    lsb = int(range_match.group(2))
    width = abs(msb - lsb) + 1
    return msb, lsb, width


def _parse_memory_value(value_str: str) -> int:
    """Parse a memory value string supporting binary, hex, and decimal formats."""
    value_clean = value_str.replace("_", "")
    # Plain binary (only 0s and 1s, no prefix)
    if re.fullmatch(r"[01]+", value_clean):
        return int(value_clean, 2)
    # Use Python's auto-detection for 0b, 0x, 0o prefixes and decimal
    return int(value_clean, 0)


def load_memory_txt_file(file_path: str, word_width: int, depth: int) -> List[int]:
    """Load plain-text memory initialization data."""
    memory = [0] * depth
    if not file_path:
        return memory

    with open(file_path, "r", encoding="utf-8") as mem_file:
        lines = mem_file.readlines()

    current_address = 0
    max_word = (1 << word_width) - 1 if word_width > 0 else 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        # Optional address override syntax: <addr>:<value>
        if ":" in line:
            addr_str, value_str = line.split(":", 1)
            address = int(addr_str.strip(), 0)
            value_str = value_str.strip()
        else:
            value_str = line
            address = current_address

        if address < 0 or address >= depth:
            continue

        memory[address] = _parse_memory_value(value_str) & max_word
        current_address = address + 1

    return memory


def normalize_memory_bindings(test_data: Any, test_dir: str, default_module: str = "") -> List[Dict[str, Any]]:
    """Normalize memory init entries from test JSON."""
    if not isinstance(test_data, dict):
        return []

    normalized: List[Dict[str, Any]] = []

    def _add_binding(entry: Dict[str, Any], mem_type: str):
        if not isinstance(entry, dict):
            return
        file_value = entry.get("file") or entry.get("path")
        if not file_value:
            return
        file_path = file_value
        if not os.path.isabs(file_path):
            file_path = os.path.normpath(os.path.join(test_dir, file_path))
        normalized.append(
            {
                "type": (entry.get("type") or mem_type or "ram").lower(),
                "module": entry.get("module") or default_module or "",
                "instance": entry.get("instance") or entry.get("instance_path") or "",
                "memory": entry.get("memory") or entry.get("name") or "",
                "file": file_path,
            }
        )

    memory_inits = test_data.get("memory_init", [])
    if isinstance(memory_inits, list):
        for init_entry in memory_inits:
            _add_binding(init_entry, init_entry.get("type", "ram") if isinstance(init_entry, dict) else "ram")

    def _process_entries(entries: Any, mem_type: str):
        """Process dict or list of memory entries."""
        if isinstance(entries, dict):
            _add_binding(entries, mem_type)
        elif isinstance(entries, list):
            for entry in entries:
                _add_binding(entry, mem_type)

    memory_files = test_data.get("memory_files", {})
    if isinstance(memory_files, dict):
        for mem_type in ("rom", "ram"):
            _process_entries(memory_files.get(mem_type, []), mem_type)

    # Backward/short-form support: top-level rom/ram blocks.
    for mem_type in ("rom", "ram"):
        _process_entries(test_data.get(mem_type), mem_type)

    return normalized


def clear_module_cache():
    """Clear the global module cache. Useful for testing or when modules change."""
    global GLOBAL_MODULE_CACHE
    GLOBAL_MODULE_CACHE.clear()


class SystemVerilogParser:
    """Parser for a subset of SystemVerilog focused on basic combinational logic."""

    def __init__(self):
        self._reset_parse_state()

    def _reset_parse_state(self):
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
        self.combinational_blocks = []  # Track always_comb blocks
        self.clock_signals = set()  # Track identified clock signals
        self.memory_arrays = {}
        self.filepath = ""

    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse a SystemVerilog file and extract module information.

        Args:
            filepath: Path to the .sv file

        Returns:
            Dictionary containing module info: name, inputs, outputs, assignments
        """
        self._reset_parse_state()
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

        # Parse reg/logic signal declarations
        self._parse_signal_declarations(content)

        # Parse memory array declarations
        self._parse_memory_arrays(content)

        # Parse assign statements
        self._parse_assignments(content)

        # Parse module instantiations
        self._parse_instantiations(content)
        
        # Parse sequential logic blocks
        self._parse_sequential_blocks(content)

        # Parse combinational logic blocks
        self._parse_combinational_blocks(content)

        return {
            "name": self.module_name,
            "inputs": self.inputs.copy(),
            "outputs": self.outputs.copy(),
            "assignments": self.assignments.copy(),
            "slice_assignments": self.slice_assignments.copy(),
            "concat_assignments": self.concat_assignments.copy(),
            "instantiations": self.instantiations.copy(),
            "sequential_blocks": self.sequential_blocks.copy(),
            "combinational_blocks": self.combinational_blocks.copy(),
            "clock_signals": list(self.clock_signals),
            "bus_info": self.bus_info.copy(),
            "memory_arrays": self.memory_arrays.copy(),
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

        # Tokenize the port list, including modifiers that can appear after input/output
        tokens = re.findall(
            r"\b(?:input|output|wire|logic|reg|signed|unsigned)\b|\[[^\]]+\]|\w+|,", port_list
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
            elif token in ["wire", "logic", "reg", "signed", "unsigned"]:
                # Skip modifier keywords - they're optional and don't affect simulation functionality
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

    def _is_valid_signal_name(self, name: str) -> bool:
        """Check if a name is a valid signal identifier."""
        reserved_keywords = {"input", "output", "wire", "logic", "reg", "signed", "unsigned"}
        if not name or "[" in name:
            return False
        if not re.fullmatch(r"\w+", name):
            return False
        return name not in reserved_keywords

    def _parse_signal_declarations(self, content: str):
        """Parse reg/logic declarations (excluding memory arrays)."""
        bus_decl_pattern = (
            r"\b(?:reg|logic)\b(?:\s+(?:signed|unsigned))?\s+"
            r"\[(\d+):(\d+)\]\s+([^;]+)\s*;"
        )
        for msb_str, lsb_str, name_list in re.findall(bus_decl_pattern, content):
            msb = int(msb_str)
            lsb = int(lsb_str)
            width = abs(msb - lsb) + 1
            for raw_name in name_list.split(","):
                name = raw_name.strip()
                if self._is_valid_signal_name(name) and name not in self.bus_info:
                    self.bus_info[name] = {"msb": msb, "lsb": lsb, "width": width}

        single_decl_pattern = (
            r"\b(?:reg|logic)\b(?:\s+(?:signed|unsigned))?\s+"
            r"(?!\[)([^;]+)\s*;"
        )
        for name_list in re.findall(single_decl_pattern, content):
            for raw_name in name_list.split(","):
                name = raw_name.strip()
                if self._is_valid_signal_name(name) and name not in self.bus_info:
                    self.bus_info[name] = {"msb": 0, "lsb": 0, "width": 1}

    def _parse_memory_arrays(self, content: str):
        """Parse memory array declarations like reg [7:0] mem [255:0];."""
        memory_pattern = (
            r"\b(?:reg|logic)\b(?:\s+(?:signed|unsigned))?\s*"
            r"(\[[^\]]+\])?\s+(\w+)\s*(\[[^\]]+\])\s*;"
        )
        declarations = re.findall(memory_pattern, content)

        for packed_range, memory_name, unpacked_range in declarations:
            try:
                if packed_range:
                    word_msb, word_lsb, word_width = parse_sv_range(packed_range)
                else:
                    word_msb, word_lsb, word_width = 0, 0, 1

                index_msb, index_lsb, depth = parse_sv_range(unpacked_range)
                self.memory_arrays[memory_name] = {
                    "word_msb": word_msb,
                    "word_lsb": word_lsb,
                    "word_width": word_width,
                    "index_msb": index_msb,
                    "index_lsb": index_lsb,
                    "depth": depth,
                }
            except Exception:
                continue

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
        """Parse sequential logic blocks like always_ff into executable AST."""
        pos = 0
        block_index = 0
        pattern = re.compile(r"always_ff\s*@\s*\(([^)]+)\)", re.IGNORECASE)

        while True:
            match = pattern.search(content, pos)
            if not match:
                break

            sensitivity_list = match.group(1).strip()
            clock_info = self._parse_sensitivity_list(sensitivity_list)
            body_start = self._skip_whitespace(content, match.end())

            if body_start >= len(content):
                break

            statement_ast = {"type": "block", "statements": []}
            next_pos = body_start

            if content.startswith("begin", body_start):
                begin_pos = body_start
                end_pos = self._find_matching_begin_end(content, begin_pos)
                block_body = content[begin_pos + len("begin"):end_pos].strip()
                statement_ast = self._parse_statement_block(block_body)
                next_pos = end_pos + len("end")
            else:
                statement_ast, next_pos = self._parse_statement(content, body_start)

            sequential_block = {
                "type": "always_ff",
                "clock": clock_info["clock"],
                "edge": clock_info["edge"],
                "statement": statement_ast,
                "order": block_index,
            }
            self.sequential_blocks.append(sequential_block)
            self.clock_signals.add(clock_info["clock"])
            block_index += 1
            pos = next_pos

    def _parse_combinational_blocks(self, content: str):
        """Parse always_comb blocks into executable AST."""
        pos = 0
        block_index = 0
        pattern = re.compile(r"\balways_comb\b")

        while True:
            match = pattern.search(content, pos)
            if not match:
                break

            body_start = self._skip_whitespace(content, match.end())
            if body_start >= len(content):
                break

            if content.startswith("begin", body_start):
                end_pos = self._find_matching_begin_end(content, body_start)
                block_body = content[body_start + len("begin"):end_pos].strip()
                statement_ast = self._parse_statement_block(block_body)
                next_pos = end_pos + len("end")
            else:
                statement_ast, next_pos = self._parse_statement(content, body_start)

            self.combinational_blocks.append({
                "type": "always_comb",
                "statement": statement_ast,
                "order": block_index,
            })
            block_index += 1
            pos = next_pos

    def _parse_sensitivity_list(self, sensitivity_list: str) -> Dict[str, str]:
        """Parse sensitivity list like 'posedge clk' or 'posedge clk or posedge rst'."""
        entries = [entry.strip() for entry in re.split(r"\bor\b|,", sensitivity_list) if entry.strip()]
        if not entries:
            return {"clock": "clk", "edge": "posedge"}

        first = entries[0]
        match = re.match(r"(posedge|negedge)\s+(\w+)", first)
        if match:
            return {"clock": match.group(2), "edge": match.group(1)}

        return {"clock": first, "edge": "posedge"}

    def _parse_statement_block(self, block_content: str) -> Dict[str, Any]:
        """Parse a begin/end block body into a list of statements."""
        statements = []
        pos = 0
        while True:
            pos = self._skip_whitespace(block_content, pos)
            if pos >= len(block_content):
                break
            statement, pos = self._parse_statement(block_content, pos)
            if statement and statement.get("type") != "empty":
                statements.append(statement)
        return {"type": "block", "statements": statements}

    def _parse_statement(self, text: str, pos: int) -> Tuple[Dict[str, Any], int]:
        pos = self._skip_whitespace(text, pos)
        if pos >= len(text):
            return {"type": "empty"}, pos

        if text.startswith("begin", pos):
            return self._parse_begin_block(text, pos)

        if text.startswith("if", pos) and self._is_keyword_boundary(text, pos, "if"):
            return self._parse_if_statement(text, pos)

        if text.startswith("case", pos) and self._is_keyword_boundary(text, pos, "case"):
            return self._parse_case_statement(text, pos)

        if text[pos] == ";":
            return {"type": "empty"}, pos + 1

        statement_text, next_pos = self._consume_until_semicolon(text, pos)
        parsed = self._parse_assignment_statement(statement_text)
        return parsed, next_pos

    def _parse_begin_block(self, text: str, pos: int) -> Tuple[Dict[str, Any], int]:
        begin_end = self._find_matching_begin_end(text, pos)
        inner = text[pos + len("begin"):begin_end]
        block_ast = self._parse_statement_block(inner)
        return block_ast, begin_end + len("end")

    def _parse_if_statement(self, text: str, pos: int) -> Tuple[Dict[str, Any], int]:
        cond_open = text.find("(", pos)
        if cond_open == -1:
            return {"type": "raw", "text": text[pos:].strip()}, len(text)
        condition, after_cond = self._extract_parenthesized(text, cond_open)
        then_stmt, cursor = self._parse_statement(text, after_cond)
        cursor = self._skip_whitespace(text, cursor)

        else_stmt = None
        if text.startswith("else", cursor) and self._is_keyword_boundary(text, cursor, "else"):
            else_stmt, cursor = self._parse_statement(text, cursor + len("else"))

        return {
            "type": "if",
            "condition": condition.strip(),
            "then": then_stmt,
            "else": else_stmt,
        }, cursor

    def _parse_case_statement(self, text: str, pos: int) -> Tuple[Dict[str, Any], int]:
        expr_open = text.find("(", pos)
        if expr_open == -1:
            return {"type": "raw", "text": text[pos:].strip()}, len(text)
        expression, cursor = self._extract_parenthesized(text, expr_open)

        items = []
        default_stmt = None

        while cursor < len(text):
            cursor = self._skip_whitespace(text, cursor)
            if text.startswith("endcase", cursor):
                cursor += len("endcase")
                break

            label_text, cursor = self._consume_until_colon(text, cursor)
            labels = [label.strip() for label in label_text.split(",") if label.strip()]
            stmt, cursor = self._parse_statement(text, cursor)

            if any(label == "default" for label in labels):
                default_stmt = stmt
            else:
                items.append({"labels": labels, "statement": stmt})

        return {
            "type": "case",
            "expression": expression.strip(),
            "items": items,
            "default": default_stmt,
        }, cursor

    def _parse_assignment_statement(self, statement_text: str) -> Dict[str, Any]:
        statement_text = statement_text.strip()
        if not statement_text:
            return {"type": "empty"}

        match = re.match(r"(.+?)(<=|=)(.+)", statement_text)
        if not match:
            return {"type": "raw", "text": statement_text}

        target_expr = match.group(1).strip()
        operator = match.group(2)
        rhs_expr = match.group(3).strip()
        target = self._parse_assignment_target(target_expr)

        if operator == "<=":
            return {"type": "nonblocking_assign", "target": target, "expression": rhs_expr}
        return {"type": "blocking_assign", "target": target, "expression": rhs_expr}

    def _parse_assignment_target(self, target_expr: str) -> Dict[str, Any]:
        mem_match = re.match(r"(\w+)\[(.+)\]$", target_expr)
        if mem_match:
            signal = mem_match.group(1)
            index_expr = mem_match.group(2).strip()
            if signal in self.memory_arrays:
                return {"kind": "memory", "memory": signal, "index": index_expr}

            if ":" in index_expr:
                slice_match = re.match(r"(\d+)\s*:\s*(\d+)$", index_expr)
                if slice_match:
                    return {
                        "kind": "slice",
                        "signal": signal,
                        "msb": int(slice_match.group(1)),
                        "lsb": int(slice_match.group(2)),
                    }

            bit_match = re.match(r"(\d+)$", index_expr)
            if bit_match:
                return {"kind": "bit", "signal": signal, "index": int(bit_match.group(1))}

            # Treat variable index on non-memory signals as generic index target.
            return {"kind": "indexed_signal", "signal": signal, "index": index_expr}

        return {"kind": "signal", "signal": target_expr}

    def _find_matching_begin_end(self, text: str, begin_pos: int) -> int:
        begin_count = 1
        pos = begin_pos + len("begin")

        while pos < len(text):
            begin_match = re.search(r"\bbegin\b", text[pos:])
            end_match = re.search(r"\bend\b", text[pos:])
            next_begin = pos + begin_match.start() if begin_match else float("inf")
            next_end = pos + end_match.start() if end_match else float("inf")

            if next_begin < next_end:
                begin_count += 1
                pos = next_begin + len("begin")
                continue

            if next_end != float("inf"):
                begin_count -= 1
                if begin_count == 0:
                    return next_end
                pos = next_end + len("end")
                continue

            break

        raise ValueError("Unmatched begin/end block")

    def _extract_parenthesized(self, text: str, open_paren_pos: int) -> Tuple[str, int]:
        depth = 0
        pos = open_paren_pos
        start = open_paren_pos + 1

        while pos < len(text):
            char = text[pos]
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return text[start:pos], pos + 1
            pos += 1

        raise ValueError("Unmatched parentheses in sequential block")

    def _consume_until_delimiter(
        self, text: str, pos: int, delimiter: str, error_on_missing: bool = False
    ) -> Tuple[str, int]:
        """Consume text until a delimiter is found at zero nesting depth."""
        depth_paren = 0
        depth_bracket = 0
        depth_brace = 0
        start = pos

        while pos < len(text):
            char = text[pos]
            if char == "(":
                depth_paren += 1
            elif char == ")":
                depth_paren -= 1
            elif char == "[":
                depth_bracket += 1
            elif char == "]":
                depth_bracket -= 1
            elif char == "{":
                depth_brace += 1
            elif char == "}":
                depth_brace -= 1
            elif char == delimiter and depth_paren == 0 and depth_bracket == 0 and depth_brace == 0:
                return text[start:pos], pos + 1
            pos += 1

        if error_on_missing:
            raise ValueError(f"Malformed statement: missing '{delimiter}'")
        return text[start:].strip(), len(text)

    def _consume_until_semicolon(self, text: str, pos: int) -> Tuple[str, int]:
        return self._consume_until_delimiter(text, pos, ";", error_on_missing=False)

    def _consume_until_colon(self, text: str, pos: int) -> Tuple[str, int]:
        return self._consume_until_delimiter(text, pos, ":", error_on_missing=True)

    def _skip_whitespace(self, text: str, pos: int) -> int:
        while pos < len(text) and text[pos].isspace():
            pos += 1
        return pos

    def _is_keyword_boundary(self, text: str, start: int, keyword: str) -> bool:
        end = start + len(keyword)
        if not text.startswith(keyword, start):
            return False
        before_ok = start == 0 or not (text[start - 1].isalnum() or text[start - 1] == "_")
        after_ok = end >= len(text) or not (text[end].isalnum() or text[end] == "_")
        return before_ok and after_ok


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
        memory_arrays: Dict[str, Dict[str, Any]] = None,
        module_name: str = "",
        instance_path: str = "",
        memory_bindings: List[Dict[str, Any]] = None,
        combinational_blocks: List[Dict[str, Any]] = None,
    ):
        self.inputs = inputs
        self.outputs = outputs
        self.assignments = assignments
        self.slice_assignments = slice_assignments or []
        self.concat_assignments = concat_assignments or []
        self.instantiations = instantiations or []
        self.bus_info = bus_info or {}
        self.current_file_path = current_file_path
        self.module_name = module_name or "top_module"
        self.instance_path = instance_path
        self.memory_arrays = memory_arrays or {}
        self.memory_bindings = memory_bindings or []
        self.combinational_blocks = combinational_blocks or []
        self.memory_state: Dict[str, List[int]] = {}
        self.memory_access: Dict[str, str] = {}
        self.instance_evaluators: Dict[str, Any] = {}
        self.rom_data: Optional[List[int]] = None
        self.rom_addr_port: Optional[str] = None
        self.rom_data_port: Optional[str] = None

        self._initialize_memory_state()
        self._initialize_rom_primitive()

    def _initialize_rom_primitive(self):
        """Auto-detect rom_* modules and load ROM data by naming convention."""
        if not self.module_name.startswith("rom_"):
            return
        if not self.inputs or not self.outputs:
            return

        rom_name = self.module_name[4:]
        addr_port = self.inputs[0]
        data_port = self.outputs[0]
        addr_width = self.bus_info.get(addr_port, {}).get("width", 1)
        data_width = self.bus_info.get(data_port, {}).get("width", 1)
        depth = 1 << addr_width

        data_filename = f"{rom_name}.txt"
        search_dirs = self._rom_search_dirs()
        rom_file_path = next(
            (os.path.join(d, data_filename) for d in search_dirs
             if os.path.exists(os.path.join(d, data_filename))),
            None,
        )
        if rom_file_path is None:
            raise FileNotFoundError(
                f"ROM data file '{data_filename}' not found for module '{self.module_name}'. "
                f"Searched: {search_dirs}"
            )

        self.rom_data = load_memory_txt_file(rom_file_path, data_width, depth)
        self.rom_addr_port = addr_port
        self.rom_data_port = data_port

    def _rom_search_dirs(self) -> List[str]:
        """Return directories to search for ROM data files."""
        dirs: List[str] = []
        if self.current_file_path:
            sv_dir = os.path.dirname(self.current_file_path)
            dirs.append(sv_dir)
            dirs.append(os.path.join(sv_dir, "roms"))
        dirs.append(os.path.join(os.getcwd(), "roms"))
        return dirs

    def _initialize_memory_state(self):
        for memory_name, memory_info in self.memory_arrays.items():
            depth = memory_info.get("depth", 0)
            self.memory_state[memory_name] = [0] * depth
            self.memory_access[memory_name] = "ram"
        self._apply_memory_bindings()

    def _binding_matches_instance(self, binding_instance: str) -> bool:
        if not binding_instance:
            return True
        if self.instance_path == binding_instance:
            return True
        return self.instance_path.endswith(f".{binding_instance}")

    def _apply_memory_bindings(self):
        for binding in self.memory_bindings:
            binding_module = binding.get("module", "")
            binding_instance = binding.get("instance", "")
            memory_name = binding.get("memory", "")
            file_path = binding.get("file", "")
            memory_type = (binding.get("type") or "ram").lower()

            if binding_module and binding_module != self.module_name:
                continue
            if not self._binding_matches_instance(binding_instance):
                continue
            if memory_name and memory_name not in self.memory_arrays:
                raise ValueError(
                    f"Memory binding refers to unknown memory '{memory_name}' in module '{self.module_name}'"
                )
            if not file_path:
                raise ValueError(
                    f"Memory binding missing file path for module '{self.module_name}'"
                )
            if not os.path.exists(file_path):
                raise FileNotFoundError(
                    f"Memory init file not found: {file_path}"
                )

            if memory_name:
                memory_names = [memory_name]
            else:
                memory_names = list(self.memory_arrays.keys())

            for mem_name in memory_names:
                mem_info = self.memory_arrays.get(mem_name)
                if not mem_info:
                    continue
                loaded = load_memory_txt_file(
                    file_path,
                    mem_info.get("word_width", 1),
                    mem_info.get("depth", 0),
                )
                self.memory_state[mem_name] = loaded
                self.memory_access[mem_name] = memory_type

    def configure_memory_bindings(self, memory_bindings: List[Dict[str, Any]]):
        self.memory_bindings = memory_bindings or []
        self._initialize_memory_state()
        for evaluator in self.instance_evaluators.values():
            if hasattr(evaluator, "configure_memory_bindings"):
                evaluator.configure_memory_bindings(self.memory_bindings)

    def evaluate(
        self, input_values: Dict[str, int], advance_sequential_instances: bool = True
    ) -> Dict[str, int]:
        """
        Evaluate all output expressions for given input values.

        Args:
            input_values: Dictionary mapping input names to their values (buses as integers)

        Returns:
            Dictionary mapping output names to their computed values
        """
        # ROM primitive: simple address-to-data lookup
        if self.rom_data is not None:
            addr = input_values.get(self.rom_addr_port, 0) % len(self.rom_data)
            return {self.rom_data_port: self.rom_data[addr]}

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
            self._evaluate_instantiation(
                inst, signal_values, advance_sequential_instances=advance_sequential_instances
            )

        # Evaluate all assignments (including intermediate wires) until no more changes
        # This handles cases where assignments depend on each other
        max_iterations = len(self.assignments) + len(self.combinational_blocks) * 2 + 10
        iteration = 0

        # Pre-compute comb block targets (static per AST, no need to recompute each iteration)
        comb_targets = [
            self._comb_block_targets(block) for block in self.combinational_blocks
        ]

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

            # Execute always_comb blocks
            for comb_block, targets in zip(self.combinational_blocks, comb_targets):
                snapshot = {sig: signal_values.get(sig) for sig in targets}
                self._execute_comb_statement(
                    comb_block.get("statement", {}), signal_values
                )
                for sig in targets:
                    if signal_values.get(sig) != snapshot[sig]:
                        changed = True

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

    def _execute_comb_statement(
        self, statement: Dict[str, Any], signal_values: Dict[str, int]
    ):
        """Execute a combinational statement AST node, updating signal_values in place."""
        stype = statement.get("type")

        if stype == "block":
            for child in statement.get("statements", []):
                self._execute_comb_statement(child, signal_values)
            return

        if stype == "if":
            condition = statement.get("condition", "0")
            cond_value = self._evaluate_expression(condition, signal_values)
            branch = statement.get("then") if cond_value else statement.get("else")
            if branch:
                self._execute_comb_statement(branch, signal_values)
            return

        if stype == "case":
            case_value = self._evaluate_expression(
                statement.get("expression", "0"), signal_values
            )
            selected = None
            for item in statement.get("items", []):
                for label in item.get("labels", []):
                    if self._evaluate_expression(label, signal_values) == case_value:
                        selected = item.get("statement")
                        break
                if selected:
                    break
            if not selected:
                selected = statement.get("default")
            if selected:
                self._execute_comb_statement(selected, signal_values)
            return

        if stype in {"blocking_assign", "nonblocking_assign"}:
            target = statement.get("target", {})
            target_signal = target.get("signal")
            value = self._evaluate_expression(
                statement.get("expression", "0"), signal_values, target_signal
            )
            self._apply_comb_assignment(target, value, signal_values)
            return

    def _apply_comb_assignment(
        self, target: Dict[str, Any], value: int, signal_values: Dict[str, int]
    ):
        """Apply a parsed assignment target to signal_values (combinational context)."""
        kind = target.get("kind")
        signal_name = target.get("signal")
        if not signal_name:
            return

        if kind == "bit":
            bit_index = int(target.get("index", 0))
            current = signal_values.get(signal_name, 0)
            if value & 1:
                signal_values[signal_name] = current | (1 << bit_index)
            else:
                signal_values[signal_name] = current & ~(1 << bit_index)
        elif kind == "slice":
            msb = int(target.get("msb", 0))
            lsb = int(target.get("lsb", 0))
            width = abs(msb - lsb) + 1
            shift = min(msb, lsb)
            mask = (1 << width) - 1
            current = signal_values.get(signal_name, 0)
            signal_values[signal_name] = (current & ~(mask << shift)) | ((value & mask) << shift)
        else:
            width = self.bus_info.get(signal_name, {}).get("width", 1)
            signal_values[signal_name] = value & ((1 << width) - 1)

        # Expand bus bits for consistency
        if signal_name in self.bus_info and self.bus_info[signal_name].get("width", 1) > 1:
            self._expand_bus_to_bits(signal_name, signal_values[signal_name], signal_values)

    def _comb_block_targets(self, block: Dict[str, Any]) -> set:
        """Collect all target signal names from a combinational block's AST."""
        targets: set = set()

        def collect(stmt: Dict[str, Any]):
            stype = stmt.get("type")
            if stype in {"blocking_assign", "nonblocking_assign"}:
                sig = stmt.get("target", {}).get("signal")
                if sig:
                    targets.add(sig)
            elif stype == "block":
                for child in stmt.get("statements", []):
                    collect(child)
            elif stype == "if":
                if stmt.get("then"):
                    collect(stmt["then"])
                if stmt.get("else"):
                    collect(stmt["else"])
            elif stype == "case":
                for item in stmt.get("items", []):
                    collect(item.get("statement", {}))
                if stmt.get("default"):
                    collect(stmt["default"])

        collect(block.get("statement", {}))
        return targets

    def _evaluate_expression(
        self, expression: str, signal_values: Dict[str, int], target_signal: str = None
    ) -> int:
        """Evaluate a single SystemVerilog expression."""
        eval_expr = expression.strip()

        # Handle simple bus-to-bus assignment (like Y = A)
        if eval_expr in signal_values:
            return signal_values[eval_expr]

        # Handle concatenation expressions like {a, b, c}
        if eval_expr.startswith("{") and eval_expr.endswith("}"):
            return self._evaluate_concatenation(eval_expr, signal_values)

        # Handle memory reads like mem[address]
        memory_access_pattern = r"(\w+)\[([^\[\]:]+)\]"

        def replace_memory_access(match):
            memory_name = match.group(1)
            index_expr = match.group(2).strip()
            if memory_name not in self.memory_state:
                return match.group(0)
            try:
                index_value = self._evaluate_expression(index_expr, signal_values)
            except Exception:
                index_value = 0
            memory_data = self.memory_state.get(memory_name, [])
            if not memory_data:
                return "0"
            index_value = max(0, min(len(memory_data) - 1, int(index_value)))
            return str(memory_data[index_value])

        eval_expr = re.sub(memory_access_pattern, replace_memory_access, eval_expr)

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

        # Replace SystemVerilog literal constants
        literal_pattern = r"(\d+)'([bhdBHD])([0-9a-fA-F_xXzZ]+)"

        def replace_literal(match):
            width = int(match.group(1))
            base = match.group(2).lower()
            value_str = match.group(3).replace("_", "").lower().replace("x", "0").replace("z", "0")
            if base == "b":
                value = int(value_str, 2)
            elif base == "h":
                value = int(value_str, 16)
            else:
                value = int(value_str, 10)
            return str(value & ((1 << width) - 1))

        eval_expr = re.sub(literal_pattern, replace_literal, eval_expr)

        # Replace identifiers with current values
        for signal_name, value in signal_values.items():
            if "[" not in signal_name:
                eval_expr = re.sub(
                    r"\b" + re.escape(signal_name) + r"\b", str(value), eval_expr
                )

        # Convert ternary operator (after slices/literals are resolved, so : is unambiguous)
        if "?" in eval_expr:
            eval_expr = self._convert_ternary(eval_expr)

        # Convert SystemVerilog operators to Python equivalents
        eval_expr = self._convert_operators(eval_expr)

        try:
            result = eval(eval_expr)
            result = int(result)

            # Apply bit masking based on target signal width
            if target_signal:
                if target_signal in self.bus_info:
                    width = self.bus_info[target_signal].get("width", 1)
                    if width > 1:
                        return result & ((1 << width) - 1)
                return result & 1

            # Expressions without explicit assignment target keep full width
            return result
        except Exception as e:
            raise ValueError(f"Error evaluating expression '{expression}': {e}")

    def _convert_operators(self, expression: str) -> str:
        """Convert SystemVerilog operators to Python equivalents."""
        # Logical operators
        expression = expression.replace("&&", " and ")
        expression = expression.replace("||", " or ")
        expression = re.sub(r"(?<![=!<>])!(?!=)", " not ", expression)

        return expression

    def _convert_ternary(self, expression: str) -> str:
        """Convert SV ternary `cond ? true_val : false_val` to Python `((true_val) if (cond) else (false_val))`."""
        # Process right-to-left (ternary is right-associative in SV)
        q_pos = expression.rfind("?")
        if q_pos == -1:
            return expression
        cond = expression[:q_pos].strip()
        rest = expression[q_pos + 1:].strip()
        colon_pos = self._find_ternary_colon(rest)
        if colon_pos == -1:
            return expression
        true_val = rest[:colon_pos].strip()
        false_val = rest[colon_pos + 1:].strip()
        # Recursively handle nested ternaries in the condition part
        if "?" in cond:
            cond = self._convert_ternary(cond)
        if "?" in false_val:
            false_val = self._convert_ternary(false_val)
        if "?" in true_val:
            true_val = self._convert_ternary(true_val)
        return f"(({true_val}) if ({cond}) else ({false_val}))"

    def _find_ternary_colon(self, text: str) -> int:
        """Find the colon matching a ternary '?' while respecting paren/bracket nesting."""
        depth = 0
        for i, ch in enumerate(text):
            if ch in "({[":
                depth += 1
            elif ch in ")}]":
                depth -= 1
            elif ch == ":" and depth == 0:
                return i
        return -1

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
        self,
        inst: Dict[str, Any],
        signal_values: Dict[str, int],
        advance_sequential_instances: bool = True,
    ):
        """Evaluate a module instantiation with persistent per-instance state."""
        module_type = inst["module_type"]
        connections = inst["connections"]
        instance_name = inst.get("instance_name", "unknown")
        instance_path = (
            f"{self.instance_path}.{instance_name}" if self.instance_path else instance_name
        )

        if module_type not in GLOBAL_MODULE_CACHE:
            self._load_module(module_type)
        if module_type not in GLOBAL_MODULE_CACHE:
            raise ValueError(f"Could not load module '{module_type}' for instance '{instance_name}'")

        module_info = GLOBAL_MODULE_CACHE[module_type]

        inst_input_values = {}
        for port_name, signal_name in connections.items():
            if port_name not in module_info["inputs"]:
                continue
            signal_value = self._resolve_signal_reference(signal_name, signal_values)
            if signal_value is None:
                available_signals = list(signal_values.keys())
                raise ValueError(
                    f"Signal '{signal_name}' not found for instantiation '{instance_name}' "
                    f"(port '{port_name}'). Available signals: "
                    f"{available_signals[:10]}{'...' if len(available_signals) > 10 else ''}"
                )
            inst_input_values[port_name] = signal_value

        if instance_name not in self.instance_evaluators:
            self.instance_evaluators[instance_name] = create_evaluator(
                module_info,
                filepath=self.current_file_path,
                module_name=module_info.get("name", module_type),
                instance_path=instance_path,
                memory_bindings=self.memory_bindings,
            )

        inst_evaluator = self.instance_evaluators[instance_name]
        if hasattr(inst_evaluator, "evaluate_cycle"):
            if advance_sequential_instances:
                inst_outputs = inst_evaluator.evaluate_cycle(inst_input_values)
            elif hasattr(inst_evaluator, "peek_outputs"):
                inst_outputs = inst_evaluator.peek_outputs(inst_input_values)
            else:
                inst_outputs = inst_evaluator.evaluate(inst_input_values)
        else:
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

    def _resolve_signal_reference(self, signal_name: str, signal_values: Dict[str, int]) -> Optional[int]:
        """Resolve a connected signal/expression from parent scope."""
        signal_name = signal_name.strip()

        # SystemVerilog literal
        literal_match = re.match(r"(\d+)'([bhdBHD])([0-9a-fA-F_xXzZ]+)$", signal_name)
        if literal_match:
            width = int(literal_match.group(1))
            base = literal_match.group(2).lower()
            value_str = literal_match.group(3).replace("_", "").lower().replace("x", "0").replace("z", "0")
            if base == "b":
                value = int(value_str, 2)
            elif base == "h":
                value = int(value_str, 16)
            else:
                value = int(value_str, 10)
            return value & ((1 << width) - 1)

        if signal_name in signal_values:
            return signal_values[signal_name]

        # Bus slice
        bus_slice_match = re.match(r"(\w+)\[(\d+):(\d+)\]$", signal_name)
        if bus_slice_match:
            bus_name = bus_slice_match.group(1)
            msb = int(bus_slice_match.group(2))
            lsb = int(bus_slice_match.group(3))
            if bus_name in signal_values:
                bus_value = signal_values[bus_name]
                width = abs(msb - lsb) + 1
                shift = lsb if msb >= lsb else msb
                mask = (1 << width) - 1
                return (bus_value >> shift) & mask

        # Bit select
        bit_select_match = re.match(r"(\w+)\[(\d+)\]$", signal_name)
        if bit_select_match:
            bus_name = bit_select_match.group(1)
            bit_index = int(bit_select_match.group(2))
            bit_signal_name = f"{bus_name}[{bit_index}]"
            if bit_signal_name in signal_values:
                return signal_values[bit_signal_name]
            if bus_name in signal_values:
                return (signal_values[bus_name] >> bit_index) & 1

        # Numeric literal without width
        if re.fullmatch(r"\d+", signal_name):
            return int(signal_name)

        return None

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

    def reset_instance_state(self):
        """Reset cached sub-module instance state."""
        for evaluator in self.instance_evaluators.values():
            if hasattr(evaluator, "reset_state"):
                evaluator.reset_state()
            elif hasattr(evaluator, "reset_instance_state"):
                evaluator.reset_instance_state()

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
    def __init__(
        self,
        inputs: List[str],
        outputs: List[str],
        assignments: Dict[str, str],
        instantiations: List[Dict],
        bus_info: Dict[str, Dict],
        slice_assignments: List[Dict],
        concat_assignments: List[Dict],
        sequential_blocks: List[Dict],
        clock_signals: List[str],
        filepath: str = "",
        memory_arrays: Dict[str, Dict[str, Any]] = None,
        module_name: str = "",
        instance_path: str = "",
        memory_bindings: List[Dict[str, Any]] = None,
        combinational_blocks: List[Dict[str, Any]] = None,
    ):
        self.inputs = inputs
        self.outputs = outputs
        self.sequential_blocks = sorted(sequential_blocks or [], key=lambda b: b.get("order", 0))
        self.clock_signals = set(clock_signals or [])
        self.bus_info = bus_info or {}
        self.module_name = module_name or "top_module"
        self.instance_path = instance_path

        self.comb_evaluator = LogicEvaluator(
            inputs,
            outputs,
            assignments,
            instantiations,
            bus_info,
            slice_assignments,
            concat_assignments,
            filepath,
            memory_arrays or {},
            self.module_name,
            self.instance_path,
            memory_bindings or [],
            combinational_blocks or [],
        )
        self.memory_arrays = self.comb_evaluator.memory_arrays

        self.state_signals = self._collect_state_signals()
        self.state: Dict[str, int] = {}
        self.reset_state()

    def _collect_state_signals(self) -> set:
        signals = set(self.outputs)

        def collect_from_statement(statement: Dict[str, Any]):
            stype = statement.get("type")
            if stype in {"nonblocking_assign", "blocking_assign"}:
                target = statement.get("target", {})
                kind = target.get("kind")
                if kind in {"signal", "bit", "slice", "indexed_signal"}:
                    signals.add(target.get("signal"))
            elif stype == "block":
                for child in statement.get("statements", []):
                    collect_from_statement(child)
            elif stype == "if":
                if statement.get("then"):
                    collect_from_statement(statement["then"])
                if statement.get("else"):
                    collect_from_statement(statement["else"])
            elif stype == "case":
                for item in statement.get("items", []):
                    collect_from_statement(item.get("statement", {}))
                if statement.get("default"):
                    collect_from_statement(statement["default"])

        for block in self.sequential_blocks:
            collect_from_statement(block.get("statement", {}))

        return {signal for signal in signals if signal}

    def _expand_known_buses(self, signal_values: Dict[str, int]):
        for signal_name, value in list(signal_values.items()):
            if (
                signal_name in self.bus_info
                and self.bus_info[signal_name].get("width", 1) > 1
                and "[" not in signal_name
            ):
                self.comb_evaluator._expand_bus_to_bits(signal_name, value, signal_values)

    def _clock_edge_active(self, block: Dict[str, Any], input_values: Dict[str, int]) -> bool:
        clock = block.get("clock")
        edge = block.get("edge", "posedge")
        if not clock or clock not in input_values:
            return True
        clock_value = input_values.get(clock, 0)
        if edge == "negedge":
            return clock_value == 0
        return clock_value == 1

    def evaluate_cycle(self, input_values: Dict[str, int]) -> Dict[str, int]:
        """Evaluate one clock cycle with nonblocking scheduling semantics."""
        current_signals = {**self.state, **input_values}
        self._expand_known_buses(current_signals)

        comb_outputs = self.comb_evaluator.evaluate(
            current_signals, advance_sequential_instances=True
        )
        snapshot = {**current_signals, **comb_outputs}
        self._expand_known_buses(snapshot)

        blocking_updates: Dict[str, int] = {}
        nonblocking_updates: Dict[str, int] = {}
        blocking_mem_updates: Dict[Tuple[str, int], int] = {}
        nonblocking_mem_updates: Dict[Tuple[str, int], int] = {}

        for block in self.sequential_blocks:
            if block.get("type") != "always_ff":
                continue
            if not self._clock_edge_active(block, input_values):
                continue

            local_context = snapshot.copy()
            self._execute_statement(
                block.get("statement", {}),
                local_context,
                blocking_updates,
                nonblocking_updates,
                blocking_mem_updates,
                nonblocking_mem_updates,
            )

        next_state = self.state.copy()
        self._commit_updates(next_state, blocking_updates)
        self._commit_memory_updates(blocking_mem_updates)
        self._commit_updates(next_state, nonblocking_updates)
        self._commit_memory_updates(nonblocking_mem_updates)
        self.state = next_state

        post_signals = {**self.state, **input_values}
        self._expand_known_buses(post_signals)
        post_outputs = self.comb_evaluator.evaluate(
            post_signals, advance_sequential_instances=False
        )

        output_values: Dict[str, int] = {}
        for output in self.outputs:
            if output in post_outputs:
                output_values[output] = post_outputs[output]
            elif output in self.state:
                output_values[output] = self.state[output]
            elif output in self.bus_info and self.bus_info[output].get("width", 1) > 1:
                output_values[output] = self.comb_evaluator._collect_bus_from_bits(output, post_signals)
            else:
                output_values[output] = 0

        return output_values

    def _execute_statement(
        self,
        statement: Dict[str, Any],
        local_context: Dict[str, int],
        blocking_updates: Dict[str, int],
        nonblocking_updates: Dict[str, int],
        blocking_mem_updates: Dict[Tuple[str, int], int],
        nonblocking_mem_updates: Dict[Tuple[str, int], int],
    ):
        stype = statement.get("type")

        if stype == "block":
            for child in statement.get("statements", []):
                self._execute_statement(
                    child,
                    local_context,
                    blocking_updates,
                    nonblocking_updates,
                    blocking_mem_updates,
                    nonblocking_mem_updates,
                )
            return

        if stype == "if":
            condition = statement.get("condition", "0")
            cond_value = self.comb_evaluator._evaluate_expression(condition, local_context)
            branch = statement.get("then") if cond_value else statement.get("else")
            if branch:
                self._execute_statement(
                    branch,
                    local_context,
                    blocking_updates,
                    nonblocking_updates,
                    blocking_mem_updates,
                    nonblocking_mem_updates,
                )
            return

        if stype == "case":
            case_value = self.comb_evaluator._evaluate_expression(statement.get("expression", "0"), local_context)
            selected = None
            for item in statement.get("items", []):
                labels = item.get("labels", [])
                for label in labels:
                    label_value = self.comb_evaluator._evaluate_expression(label, local_context)
                    if label_value == case_value:
                        selected = item.get("statement")
                        break
                if selected:
                    break
            if not selected:
                selected = statement.get("default")
            if selected:
                self._execute_statement(
                    selected,
                    local_context,
                    blocking_updates,
                    nonblocking_updates,
                    blocking_mem_updates,
                    nonblocking_mem_updates,
                )
            return

        if stype in {"blocking_assign", "nonblocking_assign"}:
            target = statement.get("target", {})
            target_signal = target.get("signal")
            value = self.comb_evaluator._evaluate_expression(
                statement.get("expression", "0"),
                local_context,
                target_signal,
            )

            if stype == "blocking_assign":
                self._record_assignment(blocking_updates, blocking_mem_updates, target, value, local_context)
                self._apply_to_context(local_context, target, value)
            else:
                self._record_assignment(nonblocking_updates, nonblocking_mem_updates, target, value, local_context)
            return

    def _record_assignment(
        self,
        signal_updates: Dict[str, int],
        memory_updates: Dict[Tuple[str, int], int],
        target: Dict[str, Any],
        value: int,
        context: Dict[str, int],
    ):
        kind = target.get("kind")
        if kind == "memory":
            memory_name = target.get("memory")
            index_expr = target.get("index", "0")
            index_value = self.comb_evaluator._evaluate_expression(index_expr, context)
            memory_updates[(memory_name, int(index_value))] = value
            return

        signal_name = target.get("signal")
        if not signal_name:
            return
        signal_updates[signal_name] = self._apply_target_transform(signal_name, target, value, signal_updates.get(signal_name))

    def _apply_target_transform(
        self,
        signal_name: str,
        target: Dict[str, Any],
        value: int,
        existing_signal_value: Optional[int] = None,
    ) -> int:
        kind = target.get("kind")
        current_value = existing_signal_value
        if current_value is None:
            current_value = self.state.get(signal_name, 0)

        if kind == "bit":
            bit_index = int(target.get("index", 0))
            if value & 1:
                return current_value | (1 << bit_index)
            return current_value & ~(1 << bit_index)

        if kind == "slice":
            msb = int(target.get("msb", 0))
            lsb = int(target.get("lsb", 0))
            width = abs(msb - lsb) + 1
            shift = min(msb, lsb)
            mask = (1 << width) - 1
            return (current_value & ~(mask << shift)) | ((value & mask) << shift)

        if signal_name in self.bus_info:
            width = self.bus_info[signal_name].get("width", 1)
            if width > 1:
                return value & ((1 << width) - 1)
        return value & 1

    def _apply_to_context(self, context: Dict[str, int], target: Dict[str, Any], value: int):
        kind = target.get("kind")
        if kind == "memory":
            return
        signal_name = target.get("signal")
        if not signal_name:
            return
        updated = self._apply_target_transform(signal_name, target, value, context.get(signal_name))
        context[signal_name] = updated
        if signal_name in self.bus_info and self.bus_info[signal_name].get("width", 1) > 1:
            self.comb_evaluator._expand_bus_to_bits(signal_name, updated, context)
        elif kind == "bit":
            bit_index = int(target.get("index", 0))
            context[f"{signal_name}[{bit_index}]"] = value & 1

    def _commit_updates(self, next_state: Dict[str, int], updates: Dict[str, int]):
        for signal_name, value in updates.items():
            next_state[signal_name] = value

    def _commit_memory_updates(self, memory_updates: Dict[Tuple[str, int], int]):
        for (memory_name, index), value in memory_updates.items():
            if memory_name not in self.comb_evaluator.memory_state:
                continue
            if self.comb_evaluator.memory_access.get(memory_name) == "rom":
                continue
            mem_data = self.comb_evaluator.memory_state[memory_name]
            if index < 0 or index >= len(mem_data):
                continue
            word_width = self.memory_arrays.get(memory_name, {}).get("word_width", 1)
            mem_data[index] = value & ((1 << word_width) - 1)

    def configure_memory_bindings(self, memory_bindings: List[Dict[str, Any]]):
        self.comb_evaluator.configure_memory_bindings(memory_bindings)
        self.reset_state()

    def reset_state(self):
        """Reset sequential signal state and nested instance state."""
        self.state = {signal_name: 0 for signal_name in self.state_signals}
        self.comb_evaluator._initialize_memory_state()
        self.comb_evaluator.reset_instance_state()

    def count_nand_gates(self) -> int:
        """Count NAND gates by delegating to the combinational evaluator."""
        return self.comb_evaluator.count_nand_gates()

    def evaluate(self, input_values: Dict[str, int]) -> Dict[str, int]:
        """Compatibility wrapper - evaluates one cycle for truth table generation."""
        return self.evaluate_cycle(input_values)

    def peek_outputs(self, input_values: Dict[str, int]) -> Dict[str, int]:
        """Read current outputs without advancing sequential state."""
        signals = {**self.state, **input_values}
        self._expand_known_buses(signals)
        comb_outputs = self.comb_evaluator.evaluate(
            signals, advance_sequential_instances=False
        )
        result = {}
        for output in self.outputs:
            if output in comb_outputs:
                result[output] = comb_outputs[output]
            elif output in self.state:
                result[output] = self.state[output]
            else:
                result[output] = 0
        return result


def _has_sequential_submodules(module_info: Dict[str, Any]) -> bool:
    """Check if any instantiated sub-modules appear to be sequential (registers)."""
    for inst in module_info.get("instantiations", []):
        module_type = inst["module_type"].lower()
        if "register" in module_type or "reg" in module_type:
            return True
    return False


def create_evaluator(
    module_info: Dict[str, Any],
    filepath: str = "",
    module_name: str = "",
    instance_path: str = "",
    memory_bindings: List[Dict[str, Any]] = None,
    check_submodules: bool = False,
):
    """Create the appropriate evaluator (sequential or combinational) for a parsed module.

    Args:
        module_info: Parsed module dictionary from SystemVerilogParser.
        filepath: Path to the SystemVerilog source file.
        module_name: Override for module name (defaults to module_info["name"]).
        instance_path: Hierarchical instance path for sub-module instantiation.
        memory_bindings: Memory initialization bindings.
        check_submodules: Also check instantiated sub-modules for sequential hints.

    Returns:
        A LogicEvaluator or SequentialLogicEvaluator instance.
    """
    is_sequential = bool(
        module_info.get("sequential_blocks") or module_info.get("clock_signals")
    )
    if not is_sequential and check_submodules:
        is_sequential = _has_sequential_submodules(module_info)

    resolved_name = module_name or module_info.get("name", "")

    if is_sequential:
        return SequentialLogicEvaluator(
            module_info["inputs"],
            module_info["outputs"],
            module_info["assignments"],
            module_info.get("instantiations", []),
            module_info.get("bus_info", {}),
            module_info.get("slice_assignments", []),
            module_info.get("concat_assignments", []),
            module_info.get("sequential_blocks", []),
            module_info.get("clock_signals", []),
            filepath,
            module_info.get("memory_arrays", {}),
            resolved_name,
            instance_path,
            memory_bindings or [],
            module_info.get("combinational_blocks", []),
        )

    return LogicEvaluator(
        module_info["inputs"],
        module_info["outputs"],
        module_info["assignments"],
        module_info.get("instantiations", []),
        module_info.get("bus_info", {}),
        module_info.get("slice_assignments", []),
        module_info.get("concat_assignments", []),
        filepath,
        module_info.get("memory_arrays", {}),
        resolved_name,
        instance_path,
        memory_bindings or [],
        module_info.get("combinational_blocks", []),
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
        
        ax.set_yticklabels(signal_labels, fontsize=14, fontweight='bold')

        # Professional time axis
        ax.set_xticks([i + 0.5 for i in range(num_cycles)])
        ax.set_xticklabels([f'{i}' for i in range(num_cycles)], fontsize=13)

        # Clean professional styling
        ax.set_xlabel('Clock Cycle', fontsize=16, fontweight='bold', color='#2C3E50')
        ax.set_ylabel('Signals', fontsize=16, fontweight='bold', color='#2C3E50')
        
        # Remove all spines for ultra-clean look
        for spine in ax.spines.values():
            spine.set_visible(False)
        
        # Professional title
        plt.title(f'Digital Waveform - {Path(output_path).stem}',
                 fontsize=20, fontweight='bold', color='#2C3E50', pad=25)
        
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
                fontsize = 13
            else:  # Larger values
                bbox_props = dict(boxstyle='round,pad=0.25', facecolor=color, alpha=0.9, edgecolor='white')
                fontsize = 12

            ax.text(x_center, y_center, str(value), ha='center', va='center',
                   fontsize=fontsize, fontweight='bold', color='white', bbox=bbox_props)


class TestRunner:
    """Runs test cases from JSON files against the simulator."""

    def __init__(self, evaluator: LogicEvaluator):
        self.evaluator = evaluator
        self.test_cycles = []  # Store test cycles for waveform generation
        self.loaded_test_file = ""

    def load_tests(self, test_file: str) -> List[Dict[str, Any]]:
        """Load test cases from a JSON file."""
        try:
            with open(test_file, "r", encoding="utf-8") as f:
                tests = json.load(f)
            self.loaded_test_file = test_file
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
        # Configure ROM/RAM bindings before running cycles.
        test_dir = os.path.dirname(self.loaded_test_file) if self.loaded_test_file else os.getcwd()
        default_module = getattr(self.evaluator, "module_name", "")
        memory_bindings = normalize_memory_bindings(tests, test_dir, default_module)
        if hasattr(self.evaluator, "configure_memory_bindings"):
            self.evaluator.configure_memory_bindings(memory_bindings)

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
        evaluator = create_evaluator(
            module_info, filepath=args.file, check_submodules=True
        )

        is_sequential = hasattr(evaluator, 'evaluate_cycle')
        if is_sequential:
            print(f"Sequential blocks detected: {len(module_info.get('sequential_blocks', []))}")
            print(f"Clock signals: {list(module_info.get('clock_signals', []))}")

        # Count NAND gates
        nand_count = evaluator.count_nand_gates()
        print(f"\nNAND Gate Count: {nand_count}")

        # Generate and display truth table (only for combinational logic)
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
