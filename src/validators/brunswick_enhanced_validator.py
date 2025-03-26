"""
Enhanced validation rules for Brunswick data
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import logging

@dataclass
class ValidationRule:
    field: str
    rule_type: str
    value: Any
    error_message: str
    severity: str = "error"  # error, warning, info

@dataclass
class ValidationResult:
    field: str
    is_valid: bool
    message: str
    severity: str
    value: Any = None

class BrunswickEnhancedValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize validation rules
        self.business_rules = self._init_business_rules()
        self.property_rules = self._init_property_rules()
        self.license_rules = self._init_license_rules()
        
    def validate_business(self, data: Dict) -> List[ValidationResult]:
        """Validate business data"""
        results = []
        
        # Required fields
        required_fields = {
            'name': 'Business name is required',
            'address': 'Business address is required',
            'type': 'Business type is required'
        }
        
        for field, message in required_fields.items():
            if not data.get(field):
                results.append(
                    ValidationResult(
                        field=field,
                        is_valid=False,
                        message=message,
                        severity="error"
                    )
                )
                
        # Business name validation
        if name := data.get('name'):
            name_validation = self._validate_business_name(name)
            results.extend(name_validation)
            
        # Business type validation
        if btype := data.get('type'):
            type_validation = self._validate_business_type(btype, data)
            results.extend(type_validation)
            
        # Address validation
        if address := data.get('address'):
            address_validation = self._validate_address(address)
            results.extend(address_validation)
            
        return results
        
    def validate_property(self, data: Dict) -> List[ValidationResult]:
        """Validate property data"""
        results = []
        
        # Map-lot validation
        if map_lot := data.get('map_lot'):
            if not re.match(r'^\d{2,3}-[A-Z]-\d{1,3}$', map_lot):
                results.append(
                    ValidationResult(
                        field='map_lot',
                        is_valid=False,
                        message="Invalid map-lot format. Expected: XXX-X-XXX",
                        severity="error",
                        value=map_lot
                    )
                )
                
        # Assessment validation
        if assessment := data.get('assessment'):
            try:
                value = float(assessment)
                if value < 1000:
                    results.append(
                        ValidationResult(
                            field='assessment',
                            is_valid=False,
                            message="Assessment value too low",
                            severity="warning",
                            value=value
                        )
                    )
                elif value > 10000000:
                    results.append(
                        ValidationResult(
                            field='assessment',
                            is_valid=False,
                            message="Assessment value unusually high",
                            severity="warning",
                            value=value
                        )
                    )
            except ValueError:
                results.append(
                    ValidationResult(
                        field='assessment',
                        is_valid=False,
                        message="Invalid assessment value",
                        severity="error",
                        value=assessment
                    )
                )
                
        # Zoning validation
        if zone := data.get('zoning'):
            valid_zones = [
                'R1', 'R2', 'R3',  # Residential
                'C1', 'C2',        # Commercial
                'I1', 'I2',        # Industrial
                'MU',              # Mixed Use
                'RR'               # Rural Residential
            ]
            if zone not in valid_zones:
                results.append(
                    ValidationResult(
                        field='zoning',
                        is_valid=False,
                        message=f"Invalid zoning code. Must be one of: {', '.join(valid_zones)}",
                        severity="error",
                        value=zone
                    )
                )
                
        return results
        
    def validate_license(self, data: Dict) -> List[ValidationResult]:
        """Validate business license data"""
        results = []
        
        # License number format
        if number := data.get('license_number'):
            if not re.match(r'^BL\d{6}$', number):
                results.append(
                    ValidationResult(
                        field='license_number',
                        is_valid=False,
                        message="Invalid license number format. Expected: BLXXXXXX",
                        severity="error",
                        value=number
                    )
                )
                
        # Date validations
        for date_field in ['issue_date', 'expiration_date']:
            if date_value := data.get(date_field):
                try:
                    date = datetime.strptime(date_value, '%Y-%m-%d')
                    if date_field == 'issue_date' and date > datetime.now():
                        results.append(
                            ValidationResult(
                                field=date_field,
                                is_valid=False,
                                message="Issue date cannot be in the future",
                                severity="error",
                                value=date_value
                            )
                        )
                except ValueError:
                    results.append(
                        ValidationResult(
                            field=date_field,
                            is_valid=False,
                            message="Invalid date format. Use YYYY-MM-DD",
                            severity="error",
                            value=date_value
                        )
                    )
                    
        # Status validation
        if status := data.get('status'):
            valid_statuses = ['ACTIVE', 'PENDING', 'EXPIRED', 'REVOKED', 'SUSPENDED']
            if status.upper() not in valid_statuses:
                results.append(
                    ValidationResult(
                        field='status',
                        is_valid=False,
                        message=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
                        severity="error",
                        value=status
                    )
                )
                
        return results
        
    def _validate_business_name(self, name: str) -> List[ValidationResult]:
        """Validate business name"""
        results = []
        
        # Length check
        if len(name) < 2:
            results.append(
                ValidationResult(
                    field='name',
                    is_valid=False,
                    message="Business name too short",
                    severity="error",
                    value=name
                )
            )
            
        # Character check
        if not re.match(r'^[a-zA-Z0-9\s\'\-\&\.]+$', name):
            results.append(
                ValidationResult(
                    field='name',
                    is_valid=False,
                    message="Business name contains invalid characters",
                    severity="error",
                    value=name
                )
            )
            
        return results
        
    def _validate_business_type(self, btype: str, data: Dict) -> List[ValidationResult]:
        """Validate business type and required permits"""
        results = []
        
        # Type validation
        valid_types = [
            'RETAIL', 'RESTAURANT', 'SERVICE',
            'PROFESSIONAL', 'ENTERTAINMENT', 'LODGING'
        ]
        
        if btype.upper() not in valid_types:
            results.append(
                ValidationResult(
                    field='type',
                    is_valid=False,
                    message=f"Invalid business type. Must be one of: {', '.join(valid_types)}",
                    severity="error",
                    value=btype
                )
            )
            
        # Required permits check
        required_permits = {
            'RESTAURANT': ['health_inspection', 'food_license'],
            'LODGING': ['occupancy_permit', 'fire_inspection'],
            'ENTERTAINMENT': ['noise_permit', 'occupancy_permit']
        }
        
        if required := required_permits.get(btype.upper()):
            for permit in required:
                if not data.get(permit):
                    results.append(
                        ValidationResult(
                            field=permit,
                            is_valid=False,
                            message=f"Required permit missing for {btype}: {permit}",
                            severity="error"
                        )
                    )
                    
        return results
        
    def _validate_address(self, address: str) -> List[ValidationResult]:
        """Validate Brunswick address"""
        results = []
        
        # Basic format check
        if not re.match(r'^\d+\s+[A-Za-z\s]+,?\s+Brunswick,?\s+ME\s+0401[1-2]$', address):
            results.append(
                ValidationResult(
                    field='address',
                    is_valid=False,
                    message="Invalid address format",
                    severity="error",
                    value=address
                )
            )
            
        # ZIP code check
        if not re.search(r'0401[1-2]$', address):
            results.append(
                ValidationResult(
                    field='address',
                    is_valid=False,
                    message="Invalid Brunswick ZIP code",
                    severity="error",
                    value=address
                )
            )
            
        return results
        
    def _init_business_rules(self) -> List[ValidationRule]:
        """Initialize business validation rules"""
        return [
            ValidationRule(
                field="name",
                rule_type="regex",
                value=r'^[a-zA-Z0-9\s\'\-\&\.]+$',
                error_message="Invalid business name format"
            ),
            ValidationRule(
                field="type",
                rule_type="enum",
                value=[
                    'RETAIL', 'RESTAURANT', 'SERVICE',
                    'PROFESSIONAL', 'ENTERTAINMENT', 'LODGING'
                ],
                error_message="Invalid business type"
            )
        ]
        
    def _init_property_rules(self) -> List[ValidationRule]:
        """Initialize property validation rules"""
        return [
            ValidationRule(
                field="map_lot",
                rule_type="regex",
                value=r'^\d{2,3}-[A-Z]-\d{1,3}$',
                error_message="Invalid map-lot format"
            ),
            ValidationRule(
                field="zoning",
                rule_type="enum",
                value=['R1', 'R2', 'R3', 'C1', 'C2', 'I1', 'I2', 'MU', 'RR'],
                error_message="Invalid zoning code"
            )
        ]
        
    def _init_license_rules(self) -> List[ValidationRule]:
        """Initialize license validation rules"""
        return [
            ValidationRule(
                field="license_number",
                rule_type="regex",
                value=r'^BL\d{6}$',
                error_message="Invalid license number format"
            ),
            ValidationRule(
                field="status",
                rule_type="enum",
                value=['ACTIVE', 'PENDING', 'EXPIRED', 'REVOKED', 'SUSPENDED'],
                error_message="Invalid license status"
            )
        ]
