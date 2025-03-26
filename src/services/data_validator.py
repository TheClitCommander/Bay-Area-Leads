"""
Data validation service for cleaning and validating property data
"""
import logging
import re
from typing import Dict, List, Tuple
from datetime import datetime

class DataValidator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def validate_property_data(self, data: Dict) -> Tuple[bool, Dict, List[str]]:
        """Validate property data with enhanced Maine-specific rules"""
        messages = []
        is_valid = True
        cleaned_data = data.copy()
        
        # Basic required fields
        required_fields = ['parcel_id', 'property_address']
        for field in required_fields:
            if not data.get(field):
                messages.append(f"Missing required field: {field}")
                is_valid = False
        
        # Maine-specific validations
        if 'property_address' in data:
            # Validate Maine address format
            cleaned_address = self._clean_address(data['property_address'])
            if not self._validate_maine_address(cleaned_address):
                messages.append("Invalid Maine address format")
                is_valid = False
            cleaned_data['property_address'] = cleaned_address
        
        # Validate property type
        if 'property_type' in data:
            if not self._validate_property_type(data['property_type']):
                messages.append("Invalid property type for Maine")
                is_valid = False
        
        # Validate tax data
        if 'tax_data' in data:
            tax_valid, tax_messages = self._validate_tax_data(data['tax_data'])
            if not tax_valid:
                messages.extend(tax_messages)
                is_valid = False
        
        # Validate zoning
        if 'zoning' in data:
            if not self._validate_maine_zoning(data['zoning']):
                messages.append("Invalid zoning code for Maine")
                is_valid = False
        """
        Validate and clean property data
        
        Args:
            data: Property data dictionary
            
        Returns:
            Tuple containing:
            - Boolean indicating if data is valid
            - Cleaned data dictionary
            - List of validation messages
        """
        messages = []
        is_valid = True
        cleaned_data = data.copy()
        
        # Required fields
        required_fields = ['parcel_id', 'property_address']
        for field in required_fields:
            if not data.get(field):
                messages.append(f"Missing required field: {field}")
                is_valid = False
        
        # Clean and validate address
        if 'property_address' in data:
            cleaned_data['property_address'] = self._clean_address(data['property_address'])
        
        # Validate numerical fields
        numerical_fields = [
            'land_value', 'building_value', 'total_value',
            'annual_tax', 'tax_rate', 'delinquent_amount',
            'land_area', 'building_area'
        ]
        
        for field in numerical_fields:
            if field in data:
                try:
                    cleaned_data[field] = self._clean_number(data[field])
                except ValueError as e:
                    messages.append(f"Invalid {field}: {str(e)}")
                    is_valid = False
        
        # Validate dates
        date_fields = ['last_payment_date', 'assessment_year']
        for field in date_fields:
            if field in data:
                try:
                    cleaned_data[field] = self._clean_date(data[field])
                except ValueError as e:
                    messages.append(f"Invalid {field}: {str(e)}")
                    is_valid = False
        
        return is_valid, cleaned_data, messages
    
    def _clean_address(self, address: str) -> str:
        """Clean and standardize address"""
        if not address:
            return ""
            
        # Remove extra whitespace
        address = " ".join(address.split())
        
        # Convert to title case
        address = address.title()
        
        # Standardize common abbreviations
        replacements = {
            " St ": " Street ",
            " Rd ": " Road ",
            " Ave ": " Avenue ",
            " Ln ": " Lane ",
            " Dr ": " Drive "
        }
        
        for old, new in replacements.items():
            address = address.replace(old, new)
        
        return address
    
    def _clean_number(self, value: any) -> float:
        """Clean and validate numerical value"""
        if isinstance(value, (int, float)):
            return float(value)
            
        if isinstance(value, str):
            # Remove currency symbols and commas
            value = value.replace("$", "").replace(",", "")
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Could not convert {value} to number")
                
        raise ValueError(f"Invalid numerical value: {value}")
    
    def _clean_date(self, value: any) -> datetime:
        """Clean and validate date value"""
        if isinstance(value, datetime):
            return value
            
        if isinstance(value, str):
            try:
                # Try common date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Could not parse date: {value}")
            except Exception as e:
                raise ValueError(f"Invalid date format: {str(e)}")
                
        raise ValueError(f"Invalid date value: {value}")
    
    def _validate_maine_address(self, address: str) -> bool:
        """Validate Maine address format"""
        if not address:
            return False
            
        # Maine address pattern
        pattern = r'^\d+\s+[A-Za-z0-9\s]+(Street|Road|Avenue|Lane|Drive|Way|Circle|Court|Place),?\s+[A-Za-z\s]+,\s+ME\s+\d{5}$'
        return bool(re.match(pattern, address))
    
    def _validate_property_type(self, prop_type: str) -> bool:
        """Validate Maine property types"""
        valid_types = {
            'Single Family',
            'Multi Family',
            'Condo',
            'Land',
            'Commercial',
            'Industrial',
            'Agricultural',
            'Mixed Use',
            'Waterfront'
        }
        return prop_type in valid_types
    
    def _validate_tax_data(self, tax_data: Dict) -> Tuple[bool, List[str]]:
        """Validate tax data for Maine properties"""
        messages = []
        is_valid = True
        
        # Check tax rate range (typical Maine range)
        if 'tax_rate' in tax_data:
            rate = float(tax_data['tax_rate'])
            if not (10 <= rate <= 30):  # Mills per thousand
                messages.append("Tax rate outside typical Maine range")
                is_valid = False
        
        # Validate assessment ratios
        if all(k in tax_data for k in ['assessed_value', 'market_value']):
            ratio = tax_data['assessed_value'] / tax_data['market_value']
            if not (0.7 <= ratio <= 1.1):  # Maine typically assesses at 100%
                messages.append("Assessment ratio outside typical range")
                is_valid = False
        
        return is_valid, messages
    
    def _validate_maine_zoning(self, zoning: str) -> bool:
        """Validate Maine zoning codes"""
        valid_zones = {
            'R1', 'R2', 'R3', 'R4', 'R5',  # Residential
            'C1', 'C2', 'C3',                # Commercial
            'I1', 'I2',                      # Industrial
            'RR', 'RP', 'SR',                # Rural/Resource
            'MU', 'VC'                       # Mixed Use/Village
        }
        return zoning in valid_zones
    
    def validate_town_name(self, town: str) -> bool:
        """Validate town name"""
        if not town:
            return False
            
        # List of valid Maine towns (would be expanded)
        valid_towns = {
            'Brunswick', 'Bath', 'Topsham', 'Harpswell',
            'Freeport', 'Yarmouth', 'Falmouth'
        }
        
        return town.strip().title() in valid_towns
