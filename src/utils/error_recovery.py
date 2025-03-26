"""
Error recovery utilities for property data extraction
"""
from typing import Dict, List, Optional, Tuple
import re
import logging
from datetime import datetime

class ErrorRecovery:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fallback_patterns = {
            'account_number': [
                r'^\s*(\d{5,7})\s*$',  # Standard format
                r'ACCT[:\s]*(\d+)',    # With ACCT prefix
                r'ID[:\s]*(\d+)'       # With ID prefix
            ],
            'owner_name': [
                r'(?:OWNER|NAME)[:\s]*([A-Z\s&,.]+)(?=\s+\d)',  # Standard format
                r'^([A-Z\s&,.]+)(?=\s+\d)',                      # At start of line
                r'(?<=\d\s)([A-Z\s&,.]+)(?=\s+\d)'             # Between numbers
            ],
            'address': [
                r'(\d+\s+[A-Z0-9\s]+(?:ST|AVE|RD|BLVD|LN|DR|WAY|CT|CIR))',  # Standard format
                r'(?:LOC|LOCATION)[:\s]*(\d+[^,\n]+)',                        # With location prefix
                r'(?:ADD|ADDRESS)[:\s]*(\d+[^,\n]+)'                          # With address prefix
            ]
        }
        
    def attempt_recovery(self, field: str, text: str, max_attempts: int = 3) -> Optional[str]:
        """Attempt to recover a field value using multiple patterns"""
        if field not in self.fallback_patterns:
            return None
            
        for i, pattern in enumerate(self.fallback_patterns[field]):
            if i >= max_attempts:
                break
                
            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    self.logger.info(f"Recovered {field} using pattern {i+1}: {value}")
                    return value
            except Exception as e:
                self.logger.warning(f"Error in recovery attempt {i+1} for {field}: {str(e)}")
                
        return None
        
    def fix_common_errors(self, text: str) -> str:
        """Fix common OCR and formatting errors"""
        fixes = [
            (r'O(?=\d)', '0'),     # Letter O to number 0
            (r'I(?=\d)', '1'),     # Letter I to number 1
            (r'l(?=\d)', '1'),     # Letter l to number 1
            (r'S(?=\d)', '5'),     # Letter S to number 5
            (r'(?<=\d)O', '0'),    # Letter O to number 0 after digits
            (r'\s+', ' '),         # Multiple spaces to single space
            (r'[,.](?=\d)', ''),   # Remove separators before digits
        ]
        
        fixed_text = text
        for pattern, replacement in fixes:
            fixed_text = re.sub(pattern, replacement, fixed_text)
            
        return fixed_text
        
    def validate_recovered_value(self, field: str, value: str) -> Tuple[bool, str]:
        """Validate a recovered value"""
        if field == 'account_number':
            if not value.isdigit():
                return False, "Account number must contain only digits"
            if len(value) < 5 or len(value) > 7:
                return False, "Account number length must be between 5 and 7 digits"
                
        elif field == 'owner_name':
            if len(value) < 2:
                return False, "Owner name too short"
            if not re.match(r'^[A-Z0-9\s&,.-]+$', value):
                return False, "Owner name contains invalid characters"
                
        elif field == 'address':
            if not re.match(r'^\d+\s+[A-Z0-9\s]+', value):
                return False, "Address must start with a number"
                
        return True, ""
        
    def create_error_report(self, property_dict: Dict, errors: List[str]) -> Dict:
        """Create a detailed error report for manual review"""
        return {
            'property_id': property_dict.get('account_number', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'errors': errors,
            'raw_text': property_dict.get('raw_text', ''),
            'extracted_fields': {
                k: v for k, v in property_dict.items()
                if k not in ['raw_text', 'processing_error']
            },
            'recovery_attempts': [],  # To be filled by recovery process
            'needs_manual_review': True
        }
