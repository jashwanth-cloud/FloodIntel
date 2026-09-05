"""
conftest.py — pytest configuration
Adds the data_processing scripts directory to sys.path so tests can import pipeline modules.
"""
import sys
import os

# Add scripts/data_processing to path for all tests
SCRIPTS_DATA_PROC = os.path.join(
    os.path.dirname(__file__), "..", "scripts", "data_processing"
)
sys.path.insert(0, os.path.abspath(SCRIPTS_DATA_PROC))
