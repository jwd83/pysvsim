#!/usr/bin/env python3
"""
Recursive SystemVerilog File Tester

A script that recursively finds all .sv files in a directory and runs
truth table generation tests on each one using pysvsim.py.

Usage:
    python testfolder.py <directory_path> [--max-combinations N] [--verbose] [--continue-on-error]
    
Arguments:
    directory_path: Path to the directory to search recursively for .sv files
    
Options:
    --max-combinations N: Maximum number of input combinations to test (default: 64)
    --verbose: Show detailed output for each file
    --continue-on-error: Continue testing other files even if some fail
    --summary-only: Only show summary statistics, not individual results
"""

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Tuple, Dict, Optional


class TestResult:
    """Container for test results."""
    def __init__(self, file_path: str, success: bool, error_message: str = "", 
                 runtime: float = 0.0, inputs: List[str] = None, outputs: List[str] = None):
        self.file_path = file_path
        self.success = success
        self.error_message = error_message
        self.runtime = runtime
        self.inputs = inputs or []
        self.outputs = outputs or []


class SystemVerilogTester:
    """Recursively tests SystemVerilog files in a directory."""
    
    def __init__(self, max_combinations: int = 64, verbose: bool = False, 
                 continue_on_error: bool = True, summary_only: bool = False):
        self.max_combinations = max_combinations
        self.verbose = verbose
        self.continue_on_error = continue_on_error
        self.summary_only = summary_only
        self.results: List[TestResult] = []
        
    def find_sv_files(self, directory: str) -> List[str]:
        """Recursively find all .sv files in the given directory."""
        sv_files = []
        directory_path = Path(directory)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        # Use pathlib to recursively find .sv files
        for sv_file in directory_path.rglob("*.sv"):
            sv_files.append(str(sv_file))
        
        return sorted(sv_files)
    
    def test_sv_file(self, file_path: str) -> TestResult:
        """Test a single .sv file using pysvsim.py."""
        start_time = time.time()
        
        try:
            # Run pysvsim.py on the file
            cmd = [
                sys.executable, "pysvsim.py", 
                "--file", file_path,
                "--max-combinations", str(self.max_combinations)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout per file
            )
            
            runtime = time.time() - start_time
            
            if result.returncode == 0:
                # Parse output to extract inputs and outputs
                inputs, outputs = self.parse_pysvsim_output(result.stdout)
                return TestResult(file_path, True, "", runtime, inputs, outputs)
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                return TestResult(file_path, False, error_msg, runtime)
                
        except subprocess.TimeoutExpired:
            runtime = time.time() - start_time
            return TestResult(file_path, False, "Timeout (>30s)", runtime)
        except Exception as e:
            runtime = time.time() - start_time
            return TestResult(file_path, False, str(e), runtime)
    
    def parse_pysvsim_output(self, output: str) -> Tuple[List[str], List[str]]:
        """Parse pysvsim.py output to extract inputs and outputs."""
        inputs = []
        outputs = []
        
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("Inputs:"):
                # Extract inputs from "Inputs: ['a', 'b', 'c']" format
                try:
                    inputs_str = line[line.find('[')+1:line.rfind(']')]
                    inputs = [inp.strip().strip("'\"") for inp in inputs_str.split(',') if inp.strip()]
                except:
                    inputs = []
            elif line.startswith("Outputs:"):
                # Extract outputs from "Outputs: ['w', 'x', 'y', 'z']" format
                try:
                    outputs_str = line[line.find('[')+1:line.rfind(']')]
                    outputs = [out.strip().strip("'\"") for out in outputs_str.split(',') if out.strip()]
                except:
                    outputs = []
        
        return inputs, outputs
    
    def run_tests(self, directory: str) -> Dict[str, any]:
        """Run tests on all .sv files in the directory."""
        print(f"🔍 Searching for .sv files in: {directory}")
        
        try:
            sv_files = self.find_sv_files(directory)
        except (FileNotFoundError, ValueError) as e:
            print(f"❌ Error: {e}")
            return {"success": False, "error": str(e)}
        
        if not sv_files:
            print("⚠️  No .sv files found in the specified directory.")
            return {"success": True, "files_tested": 0, "results": []}
        
        print(f"📁 Found {len(sv_files)} .sv files")
        
        if not self.summary_only:
            print("\n" + "="*80)
            print("TESTING RESULTS")
            print("="*80)
        
        successful_tests = 0
        total_runtime = 0.0
        
        for i, file_path in enumerate(sv_files, 1):
            relative_path = os.path.relpath(file_path, directory)
            
            if not self.summary_only:
                print(f"\n[{i:3d}/{len(sv_files)}] Testing: {relative_path}")
            
            result = self.test_sv_file(file_path)
            self.results.append(result)
            total_runtime += result.runtime
            
            if result.success:
                successful_tests += 1
                if not self.summary_only:
                    status = "✅ PASSED"
                    if self.verbose:
                        status += f" ({result.runtime:.2f}s)"
                        if result.inputs:
                            status += f" - Inputs: {len(result.inputs)}, Outputs: {len(result.outputs)}"
                    print(f"    {status}")
            else:
                if not self.summary_only:
                    status = f"❌ FAILED ({result.runtime:.2f}s)"
                    if self.verbose:
                        status += f"\n    Error: {result.error_message}"
                    print(f"    {status}")
                
                if not self.continue_on_error:
                    print(f"\n🛑 Stopping due to error (use --continue-on-error to continue)")
                    break
        
        # Print summary
        print(f"\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"📊 Files tested: {len(self.results)}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {len(self.results) - successful_tests}")
        print(f"⏱️  Total runtime: {total_runtime:.2f}s")
        
        if successful_tests > 0:
            avg_runtime = total_runtime / len(self.results)
            print(f"📈 Average time per file: {avg_runtime:.2f}s")
        
        # Show failed files if any
        failed_results = [r for r in self.results if not r.success]
        if failed_results and not self.summary_only:
            print(f"\n❌ FAILED FILES ({len(failed_results)}):")
            for result in failed_results:
                relative_path = os.path.relpath(result.file_path, directory)
                print(f"   {relative_path}")
                if self.verbose and result.error_message:
                    print(f"     → {result.error_message}")
        
        success_rate = (successful_tests / len(self.results)) * 100 if self.results else 0
        print(f"\n🎯 Success rate: {success_rate:.1f}%")
        
        return {
            "success": True,
            "files_tested": len(self.results),
            "successful": successful_tests,
            "failed": len(self.results) - successful_tests,
            "success_rate": success_rate,
            "total_runtime": total_runtime,
            "results": self.results
        }


def main():
    """Main function to run the recursive SystemVerilog tester."""
    parser = argparse.ArgumentParser(
        description="Recursively test SystemVerilog files in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('directory', help='Directory to search for .sv files')
    parser.add_argument('--max-combinations', type=int, default=64,
                       help='Maximum number of input combinations to test (default: 64)')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed output for each file')
    parser.add_argument('--continue-on-error', action='store_true', default=True,
                       help='Continue testing other files even if some fail (default: True)')
    parser.add_argument('--stop-on-error', action='store_true',
                       help='Stop testing when the first error occurs')
    parser.add_argument('--summary-only', action='store_true',
                       help='Only show summary statistics, not individual results')
    
    args = parser.parse_args()
    
    # Handle stop-on-error flag
    continue_on_error = not args.stop_on_error if args.stop_on_error else args.continue_on_error
    
    print("🧪 SystemVerilog Recursive Tester")
    print("=" * 50)
    
    tester = SystemVerilogTester(
        max_combinations=args.max_combinations,
        verbose=args.verbose,
        continue_on_error=continue_on_error,
        summary_only=args.summary_only
    )
    
    try:
        results = tester.run_tests(args.directory)
        
        if results["success"] and results["files_tested"] > 0:
            # Exit with error code if there were any failures
            failed_count = results["failed"]
            sys.exit(1 if failed_count > 0 else 0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()