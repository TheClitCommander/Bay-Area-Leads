"""
Validation rules and functions for Brunswick-specific data
"""
from typing import Dict, List, Optional, Any
import re
from datetime import datetime
import usaddress
import phonenumbers
import logging
from dataclasses import dataclass
from enum import Enum

class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationResult:
    field: str
    level: ValidationLevel
    message: str
    value: Any
    expected_type: Optional[str] = None
    constraints: Optional[Dict] = None

class BrunswickDataValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Brunswick-specific patterns
        self.patterns = {
            'map_lot': r'^(\d{2,3})-([A-Z])-(\d{1,3})$',  # Example: 123-A-45
            'zip_code': r'^0401[1-2]$',  # Brunswick zip codes
            'phone': r'^\+1207\d{7}$',  # Brunswick area code
            'tax_account': r'^[A-Z]\d{4}$'  # Tax account format
        }
        
        # Valid Brunswick street names and neighborhoods
        self.valid_streets = self._load_valid_streets()
        self.valid_neighborhoods = self._load_valid_neighborhoods()
        
    def validate_business(self, business: Dict) -> List[ValidationResult]:
        """Validate business data"""
        results = []
        
        # Required fields
        required = ['name', 'address']
        for field in required:
            if not business.get(field):
                results.append(
                    ValidationResult(
                        field=field,
                        level=ValidationLevel.ERROR,
                        message=f"Missing required field: {field}",
                        value=None
                    )
                )
                
        # Business name validation
        if name := business.get('name'):
            if len(name) < 2:
                results.append(
                    ValidationResult(
                        field='name',
                        level=ValidationLevel.ERROR,
                        message="Business name too short",
                        value=name,
                        constraints={'min_length': 2}
                    )
                )
                
        # Address validation
        if address := business.get('address'):
            address_results = self._validate_brunswick_address(address)
            results.extend(address_results)
            
        # Phone validation
        if phone := business.get('phone'):
            try:
                parsed = phonenumbers.parse(phone, "US")
                if not phonenumbers.is_valid_number(parsed):
                    results.append(
                        ValidationResult(
                            field='phone',
                            level=ValidationLevel.ERROR,
                            message="Invalid phone number",
                            value=phone
                        )
                    )
                elif not str(parsed.national_number).startswith('207'):
                    results.append(
                        ValidationResult(
                            field='phone',
                            level=ValidationLevel.WARNING,
                            message="Non-Brunswick area code",
                            value=phone
                        )
                    )
            except Exception:
                results.append(
                    ValidationResult(
                        field='phone',
                        level=ValidationLevel.ERROR,
                        message="Invalid phone number format",
                        value=phone
                    )
                )
                
        return results
        
    def validate_property(self, property_data: Dict) -> List[ValidationResult]:
        """Validate property data"""
        results = []
        
        # Validate map-lot number
        if map_lot := property_data.get('map_lot'):
            if not re.match(self.patterns['map_lot'], map_lot):
                results.append(
                    ValidationResult(
                        field='map_lot',
                        level=ValidationLevel.ERROR,
                        message="Invalid map-lot format",
                        value=map_lot,
                        constraints={'pattern': self.patterns['map_lot']}
                    )
                )
                
        # Validate assessment value
        if assessment := property_data.get('assessment'):
            try:
                value = float(assessment)
                if value <= 0:
                    results.append(
                        ValidationResult(
                            field='assessment',
                            level=ValidationLevel.ERROR,
                            message="Assessment value must be positive",
                            value=assessment
                        )
                    )
            except ValueError:
                results.append(
                    ValidationResult(
                        field='assessment',
                        level=ValidationLevel.ERROR,
                        message="Invalid assessment value",
                        value=assessment,
                        expected_type='float'
                    )
                )
                
        # Validate tax account number
        if account := property_data.get('tax_account'):
            if not re.match(self.patterns['tax_account'], account):
                results.append(
                    ValidationResult(
                        field='tax_account',
                        level=ValidationLevel.ERROR,
                        message="Invalid tax account format",
                        value=account,
                        constraints={'pattern': self.patterns['tax_account']}
                    )
                )
                
        return results
        
    def validate_permit(self, permit: Dict) -> List[ValidationResult]:
        """Validate permit data"""
        results = []
        
        # Required fields
        required = ['permit_number', 'type', 'status', 'issue_date']
        for field in required:
            if not permit.get(field):
                results.append(
                    ValidationResult(
                        field=field,
                        level=ValidationLevel.ERROR,
                        message=f"Missing required field: {field}",
                        value=None
                    )
                )
                
        # Validate dates
        if issue_date := permit.get('issue_date'):
            try:
                datetime.strptime(issue_date, '%Y-%m-%d')
            except ValueError:
                results.append(
                    ValidationResult(
                        field='issue_date',
                        level=ValidationLevel.ERROR,
                        message="Invalid date format (use YYYY-MM-DD)",
                        value=issue_date
                    )
                )
                
        # Validate permit type
        valid_types = ['building', 'business', 'planning', 'zoning']
        if permit_type := permit.get('type'):
            if permit_type.lower() not in valid_types:
                results.append(
                    ValidationResult(
                        field='type',
                        level=ValidationLevel.ERROR,
                        message="Invalid permit type",
                        value=permit_type,
                        constraints={'valid_values': valid_types}
                    )
                )
                
        return results
        
    def _validate_brunswick_address(self, address: str) -> List[ValidationResult]:
        """Validate Brunswick-specific address"""
        results = []
        
        try:
            # Parse address using usaddress library
            parsed, address_type = usaddress.tag(address)
            
            # Check zip code
            if zip_code := parsed.get('ZipCode'):
                if not re.match(self.patterns['zip_code'], zip_code):
                    results.append(
                        ValidationResult(
                            field='zip_code',
                            level=ValidationLevel.ERROR,
                            message="Invalid Brunswick zip code",
                            value=zip_code,
                            constraints={'pattern': self.patterns['zip_code']}
                        )
                    )
                    
            # Validate street name
            if street_name := parsed.get('StreetName'):
                if street_name not in self.valid_streets:
                    results.append(
                        ValidationResult(
                            field='street_name',
                            level=ValidationLevel.WARNING,
                            message="Unrecognized street name",
                            value=street_name
                        )
                    )
                    
            # Check state
            if state := parsed.get('StateName'):
                if state.upper() != 'ME':
                    results.append(
                        ValidationResult(
                            field='state',
                            level=ValidationLevel.ERROR,
                            message="Address must be in Maine",
                            value=state
                        )
                    )
                    
            # Check city
            if city := parsed.get('PlaceName'):
                if city.lower() != 'brunswick':
                    results.append(
                        ValidationResult(
                            field='city',
                            level=ValidationLevel.ERROR,
                            message="Address must be in Brunswick",
                            value=city
                        )
                    )
                    
        except Exception as e:
            results.append(
                ValidationResult(
                    field='address',
                    level=ValidationLevel.ERROR,
                    message=f"Address parsing error: {str(e)}",
                    value=address
                )
            )
            
        return results
        
    def _load_valid_streets(self) -> List[str]:
        """Load list of valid Brunswick street names"""
        # This would typically load from a database or file
        # For now, return a small sample
        return [
            "Maine Street",
            "Pleasant Street",
            "Federal Street",
            "Bath Road",
            "Brunswick Landing"
        ]
        
    def _load_valid_neighborhoods(self) -> List[str]:
        """Load list of valid Brunswick neighborhoods"""
        # This would typically load from a database or file
        return [
            "Downtown",
            "Brunswick Landing",
            "Cook's Corner",
            "Jordan Acres",
            "Brunswick Heights"
        ]
