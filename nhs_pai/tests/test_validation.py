import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils import validate_practice_code, validate_bnf_code, validate_postcode

def test_validate_practice_code_failure():
    # These should return False, but the stub returns True, so this will fail
    assert validate_practice_code("TOO_LONG_CODE_123") == False
    assert validate_practice_code("INVALID$CHAR") == False
    assert validate_practice_code("") == False

def test_validate_bnf_code_failure():
    # These should return False
    assert validate_bnf_code("!@£$%^") == False
    assert validate_bnf_code("") == False

def test_validate_postcode_failure():
    # These should return False
    assert validate_postcode("INVALID POSTCODE") == False
    assert validate_postcode("12345") == False
