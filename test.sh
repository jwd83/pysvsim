#!/bin/bash
uv run test_runner.py testing/ > test_results_testing.txt
uv run test_runner.py parts/ > test_results_parts.txt
uv run test_runner.py parts/overture/ > test_results_parts_overture.txt
