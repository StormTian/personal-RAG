"""
Benchmark test fixtures and configuration.
"""

import pytest


# Benchmark configuration
pytest_benchmark = {
    "min_time": 0.1,
    "max_time": 1.0,
    "min_rounds": 5,
    "timer": "time.perf_counter",
}
