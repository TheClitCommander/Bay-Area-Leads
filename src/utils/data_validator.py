"""
Data validation utilities
"""
import re
import logging
from typing import Dict, List, Optional, Tuple

class DataValidator:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def validate_property(self, property_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate property data
        Returns: (is_valid, list of validation messages)
        """
        messages = []
        is_valid = True
        
        # Required fields
        required_fields = ['account_number', 'location']
        for field in required_fields:
            if not property_data.get(field):
                messages.append(f"Missing required field: {field}")
                is_valid = False
        
        # Account number format
        account_num = property_data.get('account_number')
        if account_num and not self._validate_account_number(account_num):
            messages.append(f"Invalid account number format: {account_num}")
            is_valid = False
        
        # Assessment value
        assessment = property_data.get('assessment')
        if assessment:
            if not isinstance(assessment, (int, float)) or assessment < 0:
                messages.append(f"Invalid assessment value: {assessment}")
                is_valid = False
        
        # Land area
        land_area = property_data.get('land_area')
        if land_area:
            if not isinstance(land_area, (int, float)) or land_area <= 0:
                messages.append(f"Invalid land area: {land_area}")
                is_valid = False
        
        # Year built
        year_built = property_data.get('year_built')
        if year_built:
            if not isinstance(year_built, int) or year_built < 1600 or year_built > 2025:
                messages.append(f"Invalid year built: {year_built}")
                is_valid = False
        
        return is_valid, messages
    
    def validate_tax_map(self, map_data: Dict) -> Tuple[bool, List[str]]:
        """Validate tax map data"""
        messages = []
        is_valid = True
        
        # Required fields
        required_fields = ['map_number', 'parcels']
        for field in required_fields:
            if not map_data.get(field):
                messages.append(f"Missing required field: {field}")
                is_valid = False
        
        # Validate parcels
        parcels = map_data.get('parcels', [])
        if not isinstance(parcels, list):
            messages.append("Parcels must be a list")
            is_valid = False
        else:
            for i, parcel in enumerate(parcels):
                parcel_valid, parcel_messages = self._validate_parcel(parcel)
                if not parcel_valid:
                    messages.extend([f"Parcel {i}: {msg}" for msg in parcel_messages])
                    is_valid = False
        
        return is_valid, messages
    
    def _validate_parcel(self, parcel: Dict) -> Tuple[bool, List[str]]:
        """Validate individual parcel data"""
        messages = []
        is_valid = True
        
        # Required parcel fields
        required_fields = ['parcel_number', 'area']
        for field in required_fields:
            if not parcel.get(field):
                messages.append(f"Missing required field: {field}")
                is_valid = False
        
        # Validate area
        area = parcel.get('area')
        if area and (not isinstance(area, (int, float)) or area <= 0):
            messages.append(f"Invalid area: {area}")
            is_valid = False
        
        return is_valid, messages
    
    def _validate_account_number(self, account_number: str) -> bool:
        """Validate account number format"""
        # Adjust pattern based on Brunswick's actual format
        return bool(re.match(r'^\d+$', str(account_number)))
    
    def cross_validate_sources(self, 
                             property_data: Dict,
                             tax_map_data: Optional[Dict] = None,
                             gis_data: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        """Cross-validate data from different sources"""
        messages = []
        is_valid = True
        
        try:
            # If we have tax map data
            if tax_map_data:
                # Compare parcel numbers
                property_parcel = property_data.get('parcel_number')
                map_parcel = tax_map_data.get('parcel_number')
                if property_parcel and map_parcel and property_parcel != map_parcel:
                    messages.append(f"Parcel number mismatch: Property={property_parcel}, Map={map_parcel}")
                    is_valid = False
                
                # Compare land areas (with tolerance)
                prop_area = property_data.get('land_area')
                map_area = tax_map_data.get('area')
                if prop_area and map_area:
                    # Allow 5% difference
                    if abs(prop_area - map_area) / prop_area > 0.05:
                        messages.append(f"Land area mismatch: Property={prop_area}, Map={map_area}")
                        is_valid = False
            
            # If we have GIS data
            if gis_data:
                # Add GIS validation logic here
                pass
            
        except Exception as e:
            self.logger.error(f"Error in cross validation: {str(e)}")
            messages.append(f"Validation error: {str(e)}")
            is_valid = False
        
        return is_valid, messages
