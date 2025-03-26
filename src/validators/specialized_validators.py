"""
Specialized validation rules for different property types and requirements
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
import logging
from shapely.geometry import Point, Polygon
import geopandas as gpd

class PropertyType(Enum):
    RESIDENTIAL = 'residential'
    COMMERCIAL = 'commercial'
    INDUSTRIAL = 'industrial'
    AGRICULTURAL = 'agricultural'
    MIXED_USE = 'mixed_use'

class ZoneType(Enum):
    RESIDENTIAL = 'R'
    COMMERCIAL = 'C'
    INDUSTRIAL = 'I'
    MIXED = 'M'
    AGRICULTURAL = 'A'

@dataclass
class ValidationContext:
    property_type: PropertyType
    zone_type: ZoneType
    tax_district: str
    current_date: datetime
    gis_data: Optional[gpd.GeoDataFrame] = None

class SpecializedValidator:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Load GIS data if available
        self.gis_data = None
        if 'gis_file' in self.config:
            try:
                self.gis_data = gpd.read_file(self.config['gis_file'])
            except Exception as e:
                self.logger.error(f"Error loading GIS data: {str(e)}")
                
    def validate_property_type(self, data: Dict, context: ValidationContext) -> List[str]:
        """Validate property based on its type"""
        warnings = []
        
        if context.property_type == PropertyType.RESIDENTIAL:
            warnings.extend(self._validate_residential(data))
        elif context.property_type == PropertyType.COMMERCIAL:
            warnings.extend(self._validate_commercial(data))
        elif context.property_type == PropertyType.INDUSTRIAL:
            warnings.extend(self._validate_industrial(data))
            
        return warnings
        
    def _validate_residential(self, data: Dict) -> List[str]:
        """Validate residential property"""
        warnings = []
        
        # Living area requirements
        sqft = data.get('square_feet', 0)
        if sqft < 400:
            warnings.append("Living area below minimum requirement of 400 sqft")
        elif sqft > 10000:
            warnings.append("Unusually large living area for residential property")
            
        # Bedroom count
        bedrooms = data.get('bedrooms', 0)
        if bedrooms == 0:
            warnings.append("No bedrooms specified for residential property")
        elif bedrooms > 10:
            warnings.append("Unusually high number of bedrooms")
            
        return warnings
        
    def validate_zoning(self, data: Dict, context: ValidationContext) -> List[str]:
        """Validate against zoning requirements"""
        warnings = []
        
        zone_reqs = self._get_zone_requirements(context.zone_type)
        
        # Check lot size
        lot_size = data.get('lot_size', 0)
        if lot_size < zone_reqs['min_lot_size']:
            warnings.append(f"Lot size below minimum requirement of {zone_reqs['min_lot_size']} sqft")
            
        # Check building height
        height = data.get('building_height', 0)
        if height > zone_reqs['max_height']:
            warnings.append(f"Building height exceeds maximum of {zone_reqs['max_height']} feet")
            
        return warnings
        
    def validate_historical(self, data: Dict, historical_data: List[Dict]) -> List[str]:
        """Validate against historical trends"""
        warnings = []
        
        if not historical_data:
            return warnings
            
        # Calculate historical averages
        avg_value = sum(h['total_value'] for h in historical_data) / len(historical_data)
        current_value = data.get('total_value', 0)
        
        # Check for unusual value changes
        if current_value > avg_value * 2:
            warnings.append(f"Current value ({current_value}) more than double historical average ({avg_value:.2f})")
        elif current_value < avg_value * 0.5:
            warnings.append(f"Current value ({current_value}) less than half historical average ({avg_value:.2f})")
            
        return warnings
        
    def validate_tax_district(self, data: Dict, context: ValidationContext) -> List[str]:
        """Validate against tax district requirements"""
        warnings = []
        
        district_rules = self._get_district_rules(context.tax_district)
        
        # Check tax rate
        tax_rate = data.get('tax_rate', 0)
        if tax_rate < district_rules['min_rate'] or tax_rate > district_rules['max_rate']:
            warnings.append(f"Tax rate {tax_rate} outside district range ({district_rules['min_rate']}-{district_rules['max_rate']})")
            
        return warnings
        
    def validate_land_use(self, data: Dict, context: ValidationContext) -> List[str]:
        """Validate property usage"""
        warnings = []
        
        # Check if use is permitted in zone
        use_code = data.get('use_code', '')
        permitted_uses = self._get_permitted_uses(context.zone_type)
        
        if use_code not in permitted_uses:
            warnings.append(f"Use code {use_code} not permitted in {context.zone_type.value} zone")
            
        return warnings
        
    def validate_environmental(self, data: Dict) -> List[str]:
        """Check environmental constraints"""
        warnings = []
        
        if self.gis_data is not None:
            try:
                # Create point from property coordinates
                point = Point(data.get('longitude', 0), data.get('latitude', 0))
                
                # Check wetlands
                wetlands = self.gis_data[self.gis_data['type'] == 'wetland']
                if any(wetlands.contains(point)):
                    warnings.append("Property contains or is adjacent to wetlands")
                    
                # Check conservation areas
                conservation = self.gis_data[self.gis_data['type'] == 'conservation']
                if any(conservation.contains(point)):
                    warnings.append("Property in conservation area")
                    
            except Exception as e:
                self.logger.error(f"Error in environmental validation: {str(e)}")
                
        return warnings
        
    def validate_building_code(self, data: Dict) -> List[str]:
        """Validate against building codes"""
        warnings = []
        
        # Check occupancy limits
        sqft = data.get('square_feet', 0)
        bedrooms = data.get('bedrooms', 0)
        bathrooms = data.get('bathrooms', 0)
        
        if sqft > 0 and bedrooms > 0:
            # Check minimum room sizes
            avg_room_size = sqft / (bedrooms + 1)  # +1 for living area
            if avg_room_size < 70:
                warnings.append(f"Average room size ({avg_room_size:.1f} sqft) below minimum requirement")
                
        # Check bathroom ratio
        if bedrooms > 0 and bathrooms > 0:
            if bathrooms < bedrooms / 2:
                warnings.append(f"Insufficient bathrooms ({bathrooms}) for number of bedrooms ({bedrooms})")
                
        return warnings
        
    def validate_special_assessment(self, data: Dict) -> List[str]:
        """Validate special tax assessments"""
        warnings = []
        
        base_value = data.get('total_value', 0)
        special_assessment = data.get('special_assessment', 0)
        
        if special_assessment > base_value * 0.5:
            warnings.append(f"Special assessment ({special_assessment}) exceeds 50% of base value ({base_value})")
            
        return warnings
        
    def validate_deed_restrictions(self, data: Dict) -> List[str]:
        """Check deed restrictions"""
        warnings = []
        
        restrictions = data.get('deed_restrictions', [])
        current_use = data.get('current_use', '')
        
        for restriction in restrictions:
            if restriction['type'] == 'use' and current_use in restriction['prohibited']:
                warnings.append(f"Current use '{current_use}' violates deed restriction")
                
        return warnings
        
    def validate_subdivision(self, data: Dict) -> List[str]:
        """Validate subdivision requirements"""
        warnings = []
        
        if data.get('is_subdivision', False):
            lot_size = data.get('lot_size', 0)
            frontage = data.get('frontage', 0)
            
            if lot_size < 5000:
                warnings.append("Subdivision lot size below minimum requirement")
                
            if frontage < 50:
                warnings.append("Subdivision frontage below minimum requirement")
                
        return warnings
        
    def _get_zone_requirements(self, zone_type: ZoneType) -> Dict:
        """Get requirements for a zone type"""
        # This would typically load from a database or config file
        return {
            ZoneType.RESIDENTIAL: {
                'min_lot_size': 5000,
                'max_height': 35,
                'setback': 20
            },
            ZoneType.COMMERCIAL: {
                'min_lot_size': 10000,
                'max_height': 50,
                'setback': 30
            },
            ZoneType.INDUSTRIAL: {
                'min_lot_size': 20000,
                'max_height': 60,
                'setback': 40
            }
        }.get(zone_type, {
            'min_lot_size': 5000,
            'max_height': 35,
            'setback': 20
        })
        
    def _get_district_rules(self, district: str) -> Dict:
        """Get rules for a tax district"""
        # This would typically load from a database or config file
        return {
            'min_rate': 0.01,
            'max_rate': 0.05,
            'assessment_frequency': 365,
            'special_conditions': []
        }
        
    def _get_permitted_uses(self, zone_type: ZoneType) -> List[str]:
        """Get permitted uses for a zone type"""
        # This would typically load from a database or config file
        return {
            ZoneType.RESIDENTIAL: ['single_family', 'multi_family', 'townhouse'],
            ZoneType.COMMERCIAL: ['retail', 'office', 'restaurant'],
            ZoneType.INDUSTRIAL: ['manufacturing', 'warehouse', 'distribution']
        }.get(zone_type, [])
