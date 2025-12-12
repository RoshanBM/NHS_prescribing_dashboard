import re

def validate_practice_code(code):
    if not code or len(code) > 15 or not code.isalnum():
        return False
    return True

def validate_bnf_code(code):
    if not code or not code.isalnum():
        return False
    return True

def validate_postcode(postcode):
    # Basic UK postcode regex
    pattern = r'^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$'
    if not postcode or not re.match(pattern, postcode, re.IGNORECASE):
        return False
    return True
