"""
Advanced validation rules for property data
"""
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime
import logging
import usaddress
import phonenumbers
from dataclasses import dataclass
from enum import Enum

class ValidationSeverity(Enum):
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'

@dataclass
class ValidationResult:
    field: str
    message: str
    severity: ValidationSeverity
    value: str
    expected_format: str

class AdvancedValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common business suffixes
        self.business_suffixes = {
            'LLC', 'INC', 'CORP', 'LTD', 'LP', 'LLP', 'PC', 'PA', 'DBA',
            'INCORPORATED', 'CORPORATION', 'COMPANY', 'LIMITED'
        }
        
        # Common street types
        self.street_types = {
            'ST', 'AVE', 'RD', 'BLVD', 'LN', 'DR', 'WAY', 'CT', 'CIR', 'TER',
            'PL', 'STREET', 'AVENUE', 'ROAD', 'BOULEVARD', 'LANE', 'DRIVE',
            'COURT', 'CIRCLE', 'TERRACE', 'PLACE'
        }
        
    def validate_property(self, property_dict: Dict) -> List[ValidationResult]:
        """Comprehensive property validation"""
        results = []
        
        # Owner validation
        if 'owner_name' in property_dict:
            results.extend(self._validate_owner(property_dict['owner_name']))
            
        # Address validation
        if 'street_address' in property_dict:
            results.extend(self._validate_address(property_dict['street_address']))
            
        # Value validation
        results.extend(self._validate_values(property_dict))
        
        # Date validation
        results.extend(self._validate_dates(property_dict))
        
        # Contact validation
        results.extend(self._validate_contact_info(property_dict))
        
        # Geographic validation
        results.extend(self._validate_geographic_info(property_dict))
        
        return results
        
    def _validate_owner(self, owner_name: str) -> List[ValidationResult]:
        """Validate owner name format"""
        results = []
        
        # Check for empty or too short
        if not owner_name or len(owner_name.strip()) < 2:
            return [ValidationResult(
                'owner_name',
                'Owner name is too short',
                ValidationSeverity.ERROR,
                owner_name,
                'Name should be at least 2 characters'
            )]
            
        # Detect if business or individual
        is_business = any(suffix in owner_name.upper().split() for suffix in self.business_suffixes)
        
        if is_business:
            # Business name validation
            if not re.match(r'^[A-Z0-9\s&,.-]+$', owner_name):
                results.append(ValidationResult(
                    'owner_name',
                    'Invalid business name format',
                    ValidationSeverity.WARNING,
                    owner_name,
                    'Only letters, numbers, spaces, &,.-'
                ))
        else:
            # Individual name validation
            if not re.match(r'^[A-Z\s,.-]+$', owner_name):
                results.append(ValidationResult(
                    'owner_name',
                    'Invalid individual name format',
                    ValidationSeverity.WARNING,
                    owner_name,
                    'Only letters, spaces, ,.-'
                ))
                
            # Check for reasonable name parts
            parts = owner_name.split()
            if len(parts) < 2:
                results.append(ValidationResult(
                    'owner_name',
                    'Name appears incomplete',
                    ValidationSeverity.WARNING,
                    owner_name,
                    'Should include first and last name'
                ))
                
        return results
        
    def _validate_address(self, address: str) -> List[ValidationResult]:
        """Validate address format using usaddress parser"""
        results = []
        
        try:
            # Parse address using usaddress
            parsed_addr = usaddress.tag(address)
            
            if not parsed_addr:
                return [ValidationResult(
                    'address',
                    'Could not parse address',
                    ValidationSeverity.ERROR,
                    address,
                    'Street number and name required'
                )]
                
            components = parsed_addr[0]
            
            # Check for required components
            required = ['AddressNumber', 'StreetName']
            for req in required:
                if req not in components:
                    results.append(ValidationResult(
                        'address',
                        f'Missing {req}',
                        ValidationSeverity.ERROR,
                        address,
                        'Complete street address required'
                    ))
                    
            # Validate street type
            if 'StreetNamePostType' in components:
                street_type = components['StreetNamePostType'].upper()
                if street_type not in self.street_types:
                    results.append(ValidationResult(
                        'address',
                        'Unknown street type',
                        ValidationSeverity.WARNING,
                        street_type,
                        f"Should be one of: {', '.join(sorted(self.street_types))}"
                    ))
                    
        except Exception as e:
            results.append(ValidationResult(
                'address',
                f'Error parsing address: {str(e)}',
                ValidationSeverity.ERROR,
                address,
                'Valid street address'
            ))
            
        return results
        
    def _validate_values(self, property_dict: Dict) -> List[ValidationResult]:
        """Validate property values"""
        results = []
        
        # Check value relationships
        value_fields = {
            'land_value': 0,
            'building_value': 0,
            'total_value': 0,
            'assessed_value': 0,
            'market_value': 0
        }
        
        # Get actual values
        for field in value_fields:
            try:
                value_fields[field] = float(property_dict.get(field, 0))
            except (ValueError, TypeError):
                results.append(ValidationResult(
                    field,
                    'Invalid numeric value',
                    ValidationSeverity.ERROR,
                    str(property_dict.get(field, '')),
                    'Numeric value required'
                ))
                
        # Validate value relationships
        if value_fields['total_value'] > 0:
            # Check if total matches components
            component_sum = value_fields['land_value'] + value_fields['building_value']
            if abs(component_sum - value_fields['total_value']) > 1:  # Allow $1 difference
                results.append(ValidationResult(
                    'total_value',
                    'Total value does not match components',
                    ValidationSeverity.WARNING,
                    f"{value_fields['total_value']} != {component_sum}",
                    'Should equal sum of land and building values'
                ))
                
        return results
        
    def _validate_dates(self, property_dict: Dict) -> List[ValidationResult]:
        """Validate date fields"""
        results = []
        date_fields = ['deed_date', 'sale_date', 'assessment_date']
        
        for field in date_fields:
            if field in property_dict:
                try:
                    date_str = property_dict[field]
                    date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    
                    # Check if date is in reasonable range
                    if date_obj.year < 1800 or date_obj.year > datetime.now().year:
                        results.append(ValidationResult(
                            field,
                            'Date outside reasonable range',
                            ValidationSeverity.WARNING,
                            date_str,
                            'Date between 1800 and present'
                        ))
                except ValueError:
                    results.append(ValidationResult(
                        field,
                        'Invalid date format',
                        ValidationSeverity.ERROR,
                        str(property_dict[field]),
                        'MM/DD/YYYY'
                    ))
                    
        return results
        
    def _validate_contact_info(self, property_dict: Dict) -> List[ValidationResult]:
        """Validate contact information"""
        results = []
        
        # Phone validation
        if 'phone' in property_dict:
            try:
                parsed = phonenumbers.parse(property_dict['phone'], "US")
                if not phonenumbers.is_valid_number(parsed):
                    results.append(ValidationResult(
                        'phone',
                        'Invalid phone number',
                        ValidationSeverity.WARNING,
                        property_dict['phone'],
                        'Valid US phone number'
                    ))
            except Exception:
                results.append(ValidationResult(
                    'phone',
                    'Could not parse phone number',
                    ValidationSeverity.WARNING,
                    property_dict['phone'],
                    'Valid US phone number'
                ))
                
        # Email validation
        if 'email' in property_dict:
            email = property_dict['email']
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                results.append(ValidationResult(
                    'email',
                    'Invalid email format',
                    ValidationSeverity.WARNING,
                    email,
                    'valid@email.com'
                ))
                
        return results
        
    def _validate_geographic_info(self, property_dict: Dict) -> List[ValidationResult]:
        """Validate geographic information"""
        results = []
        
        # Validate map/lot format
        if 'map_lot' in property_dict:
            if not re.match(r'^[A-Z][0-9]+-[0-9]+-[0-9]+-[0-9]+$', property_dict['map_lot']):
                results.append(ValidationResult(
                    'map_lot',
                    'Invalid map/lot format',
                    ValidationSeverity.ERROR,
                    property_dict['map_lot'],
                    'X##-###-###-###'
                ))
                
        # Validate coordinates if present
        if 'latitude' in property_dict and 'longitude' in property_dict:
            try:
                lat = float(property_dict['latitude'])
                lon = float(property_dict['longitude'])
                
                # Check if coordinates are in Maine
                if not (43.0 <= lat <= 47.5 and -71.0 >= lon >= -67.0):
                    results.append(ValidationResult(
                        'coordinates',
                        'Coordinates outside Maine',
                        ValidationSeverity.WARNING,
                        f"{lat}, {lon}",
                        'Maine coordinates'
                    ))
            except ValueError:
                results.append(ValidationResult(
                    'coordinates',
                    'Invalid coordinate format',
                    ValidationSeverity.ERROR,
                    f"{property_dict.get('latitude', '')}, {property_dict.get('longitude', '')}",
                    'Numeric coordinates'
                ))
                
        return results
