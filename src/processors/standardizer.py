"""
Data standardization pipeline
Ensures all data follows consistent patterns and rules
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

class DataStandardizer:
    """
    Standardizes data formats and values
    Ensures consistency across different data sources
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Load standardization rules
        self.rules = self._load_rules()
        
    def standardize(self, data: Dict, data_type: str) -> Dict:
        """
        Standardize a single record
        Applies type-specific rules and formats
        """
        try:
            if not isinstance(data, dict):
                return data
                
            # Get rules for this type
            type_rules = self.rules.get(data_type, {})
            
            # Apply rules
            standardized = {}
            for field, value in data.items():
                if field in type_rules:
                    try:
                        standardized[field] = type_rules[field](value)
                    except Exception as e:
                        self.logger.warning(f"Error standardizing {field}: {str(e)}")
                        standardized[field] = value
                else:
                    standardized[field] = value
                    
            # Add metadata
            standardized['_standardized'] = True
            standardized['_standardized_at'] = datetime.now().isoformat()
            
            return standardized
            
        except Exception as e:
            self.logger.error(f"Error standardizing data: {str(e)}")
            return data
            
    def _load_rules(self) -> Dict:
        """Load standardization rules for each data type"""
        return {
            'property': {
                'property_type': self._standardize_property_type,
                'zone_code': self._standardize_zone_code,
                'flood_zone': self._standardize_flood_zone,
                'land_use_code': self._standardize_land_use,
                'coordinates': self._standardize_coordinates
            },
            'owner': {
                'owner_type': self._standardize_owner_type,
                'business_type': self._standardize_business_type,
                'license_numbers': self._standardize_license_numbers
            },
            'transaction': {
                'transaction_type': self._standardize_transaction_type,
                'document_type': self._standardize_document_type
            },
            'permit': {
                'permit_type': self._standardize_permit_type,
                'status': self._standardize_permit_status
            },
            'violation': {
                'violation_type': self._standardize_violation_type,
                'severity': self._standardize_severity,
                'status': self._standardize_violation_status
            }
        }
        
    def _standardize_property_type(self, value: str) -> str:
        """Standardize property type classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        # Standard property types
        types = {
            'single_family': [
                'single family', 'single-family', 'sfh', 
                'single family home', 'detached'
            ],
            'multi_family': [
                'multi family', 'multi-family', 'mfh',
                'apartment', 'duplex', 'triplex'
            ],
            'commercial': [
                'commercial', 'retail', 'office', 'business',
                'industrial', 'warehouse'
            ],
            'mixed_use': [
                'mixed use', 'mixed-use', 'residential commercial',
                'live work', 'live-work'
            ],
            'vacant_land': [
                'vacant', 'land', 'lot', 'undeveloped',
                'raw land'
            ]
        }
        
        for std_type, variations in types.items():
            if any(v in value for v in variations):
                return std_type
                
        return 'other'
        
    def _standardize_zone_code(self, value: str) -> str:
        """Standardize zoning codes"""
        if not value:
            return 'unknown'
            
        value = value.upper().strip()
        
        # Brunswick zoning codes
        zones = {
            'R1': ['R-1', 'R1', 'RESIDENTIAL 1'],
            'R2': ['R-2', 'R2', 'RESIDENTIAL 2'],
            'R3': ['R-3', 'R3', 'RESIDENTIAL 3'],
            'TR1': ['TR-1', 'TR1', 'TOWN RES 1'],
            'TR2': ['TR-2', 'TR2', 'TOWN RES 2'],
            'TR3': ['TR-3', 'TR3', 'TOWN RES 3'],
            'TR4': ['TR-4', 'TR4', 'TOWN RES 4'],
            'TR5': ['TR-5', 'TR5', 'TOWN RES 5'],
            'MU2': ['MU-2', 'MU2', 'MIXED USE 2'],
            'MU3': ['MU-3', 'MU3', 'MIXED USE 3'],
            'MU4': ['MU-4', 'MU4', 'MIXED USE 4'],
            'HC1': ['HC-1', 'HC1', 'HIGHWAY COM 1'],
            'HC2': ['HC-2', 'HC2', 'HIGHWAY COM 2'],
            'TC1': ['TC-1', 'TC1', 'TOWN CENTER 1'],
            'TC2': ['TC-2', 'TC2', 'TOWN CENTER 2'],
            'TC3': ['TC-3', 'TC3', 'TOWN CENTER 3'],
            'TC4': ['TC-4', 'TC4', 'TOWN CENTER 4']
        }
        
        for std_zone, variations in zones.items():
            if any(v == value for v in variations):
                return std_zone
                
        return value
        
    def _standardize_flood_zone(self, value: str) -> str:
        """Standardize flood zone designations"""
        if not value:
            return 'unknown'
            
        value = value.upper().strip()
        
        # FEMA flood zones
        zones = {
            'A': ['A', 'A1', 'A2', 'A3', 'A4', 'A5'],
            'AE': ['AE'],
            'AH': ['AH'],
            'AO': ['AO'],
            'VE': ['VE', 'V1', 'V2', 'V3'],
            'X': ['X', 'C', 'B'],
            'D': ['D']
        }
        
        for std_zone, variations in zones.items():
            if any(v == value for v in variations):
                return std_zone
                
        return value
        
    def _standardize_land_use(self, value: str) -> str:
        """Standardize land use codes"""
        if not value:
            return 'unknown'
            
        value = value.upper().strip()
        
        # Standard land use codes
        uses = {
            'residential': ['RES', 'R', 'RESIDENTIAL'],
            'commercial': ['COM', 'C', 'COMMERCIAL'],
            'industrial': ['IND', 'I', 'INDUSTRIAL'],
            'agricultural': ['AG', 'A', 'AGRICULTURAL'],
            'vacant': ['VAC', 'V', 'VACANT'],
            'exempt': ['EX', 'E', 'EXEMPT']
        }
        
        for std_use, variations in uses.items():
            if any(v == value for v in variations):
                return std_use
                
        return value
        
    def _standardize_coordinates(self, value: Dict) -> Dict:
        """Standardize coordinate format"""
        if not value or not isinstance(value, dict):
            return {}
            
        try:
            lat = float(value.get('latitude', value.get('lat', 0)))
            lng = float(value.get('longitude', value.get('lng', 0)))
            
            return {
                'latitude': round(lat, 6),
                'longitude': round(lng, 6)
            }
        except (ValueError, TypeError):
            return {}
            
    def _standardize_owner_type(self, value: str) -> str:
        """Standardize owner type classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        types = {
            'individual': [
                'individual', 'person', 'single', 'natural person'
            ],
            'business': [
                'business', 'company', 'corporation', 'llc', 'inc',
                'corp', 'partnership'
            ],
            'trust': [
                'trust', 'estate', 'trustee', 'living trust'
            ],
            'government': [
                'government', 'city', 'state', 'federal', 'municipal'
            ],
            'non_profit': [
                'non profit', 'nonprofit', 'npo', '501c'
            ]
        }
        
        for std_type, variations in types.items():
            if any(v in value for v in variations):
                return std_type
                
        return 'other'
        
    def _standardize_business_type(self, value: str) -> str:
        """Standardize business type classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        types = {
            'llc': ['llc', 'limited liability company'],
            'corporation': ['corporation', 'corp', 'inc', 'incorporated'],
            'partnership': ['partnership', 'lp', 'llp', 'limited partnership'],
            'sole_proprietorship': ['sole proprietorship', 'dba'],
            'trust': ['trust', 'business trust', 'statutory trust']
        }
        
        for std_type, variations in types.items():
            if any(v in value for v in variations):
                return std_type
                
        return 'other'
        
    def _standardize_license_numbers(self, value: Any) -> List[str]:
        """Standardize business license number format"""
        if not value:
            return []
            
        if isinstance(value, str):
            # Split on common separators
            licenses = re.split(r'[,;\s]+', value)
        elif isinstance(value, (list, tuple)):
            licenses = value
        else:
            return []
            
        # Clean and standardize each license number
        cleaned = []
        for license in licenses:
            # Remove special characters
            clean = re.sub(r'[^\w-]', '', str(license))
            if clean:
                cleaned.append(clean.upper())
                
        return cleaned
        
    def _standardize_transaction_type(self, value: str) -> str:
        """Standardize transaction type classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        types = {
            'sale': ['sale', 'purchase', 'transfer'],
            'foreclosure': ['foreclosure', 'bank owned', 'reo'],
            'tax_lien': ['tax lien', 'tax deed', 'tax sale'],
            'quit_claim': ['quit claim', 'quitclaim'],
            'gift': ['gift', 'donation'],
            'inheritance': ['inheritance', 'estate transfer', 'probate']
        }
        
        for std_type, variations in types.items():
            if any(v in value for v in variations):
                return std_type
                
        return 'other'
        
    def _standardize_document_type(self, value: str) -> str:
        """Standardize document type classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        types = {
            'warranty_deed': ['warranty deed', 'wd'],
            'quit_claim_deed': ['quit claim deed', 'quitclaim deed', 'qcd'],
            'trustee_deed': ['trustee deed', 'trust deed'],
            'tax_deed': ['tax deed'],
            'foreclosure_deed': ['foreclosure deed', 'sheriffs deed'],
            'deed_in_lieu': ['deed in lieu', 'dil']
        }
        
        for std_type, variations in types.items():
            if any(v in value for v in variations):
                return std_type
                
        return 'other'
        
    def _standardize_permit_type(self, value: str) -> str:
        """Standardize permit type classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        types = {
            'building': ['building', 'construction', 'new construction'],
            'renovation': ['renovation', 'remodel', 'alteration'],
            'electrical': ['electrical', 'electric'],
            'plumbing': ['plumbing', 'plumb'],
            'mechanical': ['mechanical', 'hvac'],
            'demolition': ['demolition', 'demo'],
            'roofing': ['roofing', 'roof'],
            'sign': ['sign', 'signage']
        }
        
        for std_type, variations in types.items():
            if any(v in value for v in variations):
                return std_type
                
        return 'other'
        
    def _standardize_permit_status(self, value: str) -> str:
        """Standardize permit status classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        statuses = {
            'pending': ['pending', 'submitted', 'under review'],
            'approved': ['approved', 'issued'],
            'in_progress': ['in progress', 'active', 'ongoing'],
            'completed': ['completed', 'finalized', 'closed'],
            'expired': ['expired', 'lapsed'],
            'cancelled': ['cancelled', 'canceled', 'withdrawn'],
            'denied': ['denied', 'rejected']
        }
        
        for std_status, variations in statuses.items():
            if any(v in value for v in variations):
                return std_status
                
        return 'other'
        
    def _standardize_violation_type(self, value: str) -> str:
        """Standardize violation type classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        types = {
            'building': ['building code', 'construction'],
            'zoning': ['zoning', 'land use', 'setback'],
            'health': ['health', 'sanitation'],
            'fire': ['fire code', 'fire safety'],
            'occupancy': ['occupancy', 'overcrowding'],
            'maintenance': ['maintenance', 'repair'],
            'nuisance': ['nuisance', 'noise', 'trash']
        }
        
        for std_type, variations in types.items():
            if any(v in value for v in variations):
                return std_type
                
        return 'other'
        
    def _standardize_severity(self, value: str) -> str:
        """Standardize violation severity levels"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        levels = {
            'low': ['low', 'minor', 'l'],
            'medium': ['medium', 'moderate', 'm'],
            'high': ['high', 'severe', 'h'],
            'critical': ['critical', 'emergency', 'urgent']
        }
        
        for std_level, variations in levels.items():
            if any(v in value for v in variations):
                return std_level
                
        return 'unknown'
        
    def _standardize_violation_status(self, value: str) -> str:
        """Standardize violation status classifications"""
        if not value:
            return 'unknown'
            
        value = value.lower().strip()
        
        statuses = {
            'open': ['open', 'active', 'pending'],
            'warning': ['warning', 'notice'],
            'citation': ['citation', 'ticket', 'fine'],
            'hearing': ['hearing', 'court'],
            'resolved': ['resolved', 'closed', 'completed'],
            'appealed': ['appealed', 'appeal', 'disputed']
        }
        
        for std_status, variations in statuses.items():
            if any(v in value for v in variations):
                return std_status
                
        return 'other'
