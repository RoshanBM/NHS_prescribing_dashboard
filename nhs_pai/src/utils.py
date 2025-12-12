import re

# Pre-compiled regex for UK Postcodes
UK_POSTCODE_PATTERN = re.compile(r'^[A-Z]{1,2}[0-9][A-Z0-9]?\s?[0-9][A-Z]{2}$', re.IGNORECASE)

def validate_practice_code(code: str) -> bool:
    
    return bool(code and code.isalnum() and len(code) <= 15)

def validate_bnf_code(code: str) -> bool:
    
    return bool(code and code.isalnum())

def validate_postcode(postcode: str) -> bool:
    
    return bool(postcode and UK_POSTCODE_PATTERN.match(postcode))
