"""
Comprehensive property validation system including all rules
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
import logging
import numpy as np
from shapely.geometry import Point, Polygon
import requests
import json

class PropertyType(Enum):
    RESIDENTIAL = 'residential'
    COMMERCIAL = 'commercial'
    INDUSTRIAL = 'industrial'
    MIXED_USE = 'mixed_use'

class ComprehensiveValidator:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
    def validate_legal_regulatory(self, property_data: Dict) -> List[str]:
        """Validate legal and regulatory requirements"""
        warnings = []
        
        # Zoning variance validation
        if property_data.get('has_variance'):
            variance_data = property_data.get('variance_details', {})
            if not variance_data.get('approval_date'):
                warnings.append("Missing variance approval date")
            if not variance_data.get('expiration_date'):
                warnings.append("Missing variance expiration date")
                
        # Property easement validation
        easements = property_data.get('easements', [])
        for easement in easements:
            if not easement.get('recorded_date'):
                warnings.append(f"Unrecorded easement: {easement.get('type')}")
            if not easement.get('holder'):
                warnings.append(f"Missing easement holder: {easement.get('type')}")
                
        # HOA compliance
        if property_data.get('has_hoa'):
            hoa_data = property_data.get('hoa_details', {})
            if not hoa_data.get('compliance_status'):
                warnings.append("Missing HOA compliance status")
            if hoa_data.get('violations', []):
                warnings.extend([f"HOA violation: {v}" for v in hoa_data['violations']])
                
        # Municipal code compliance
        code_violations = property_data.get('code_violations', [])
        for violation in code_violations:
            if violation['status'] == 'open':
                warnings.append(f"Open code violation: {violation['description']}")
                
        return warnings
        
    def validate_financial(self, property_data: Dict) -> List[str]:
        """Validate financial aspects"""
        warnings = []
        
        # Mortgage qualification
        if property_data.get('mortgage_required'):
            income = property_data.get('buyer_income', 0)
            price = property_data.get('price', 0)
            if price > income * 4:
                warnings.append("Property price may exceed typical mortgage qualification limits")
                
        # Insurance requirements
        insurance = property_data.get('insurance', {})
        required_coverage = property_data.get('required_coverage', [])
        for coverage in required_coverage:
            if coverage not in insurance.get('coverages', []):
                warnings.append(f"Missing required insurance coverage: {coverage}")
                
        # Tax liens
        liens = property_data.get('tax_liens', [])
        if liens:
            total_lien = sum(lien['amount'] for lien in liens)
            warnings.append(f"Outstanding tax liens: ${total_lien:,.2f}")
            
        # Investment ROI
        if property_data.get('investment_property'):
            roi = self._calculate_roi(property_data)
            if roi < 0.05:
                warnings.append(f"Low ROI: {roi:.1%}")
                
        return warnings
        
    def validate_environmental(self, property_data: Dict) -> List[str]:
        """Validate environmental factors"""
        warnings = []
        
        # Solar potential
        if property_data.get('solar_analysis'):
            solar = property_data['solar_analysis']
            if solar['annual_kwh'] < 1000:
                warnings.append("Low solar energy potential")
                
        # Noise pollution
        noise = property_data.get('noise_levels', {})
        if noise.get('average_db', 0) > 65:
            warnings.append(f"High noise level: {noise['average_db']}dB")
            
        # Air quality
        air = property_data.get('air_quality', {})
        if air.get('aqi', 0) > 100:
            warnings.append(f"Poor air quality: AQI {air['aqi']}")
            
        # Soil contamination
        soil = property_data.get('soil_analysis', {})
        if soil.get('contamination_found'):
            warnings.append(f"Soil contamination detected: {soil['contaminant_type']}")
            
        # Water rights
        water = property_data.get('water_rights', {})
        if not water.get('verified'):
            warnings.append("Unverified water rights")
            
        return warnings
        
    def validate_technical(self, property_data: Dict) -> List[str]:
        """Validate technical requirements"""
        warnings = []
        
        # Smart home compatibility
        if property_data.get('smart_home_ready'):
            required_features = ['wifi', 'automation_hub', 'smart_thermostat']
            for feature in required_features:
                if feature not in property_data.get('smart_features', []):
                    warnings.append(f"Missing smart home feature: {feature}")
                    
        # Telecommunications
        telecom = property_data.get('telecommunications', {})
        if telecom.get('internet_speed', 0) < 100:
            warnings.append("Insufficient internet speed")
        if not telecom.get('fiber_available'):
            warnings.append("Fiber internet not available")
            
        # Building automation
        if property_data.get('building_automation'):
            required_systems = ['hvac', 'lighting', 'security']
            for system in required_systems:
                if system not in property_data.get('automated_systems', []):
                    warnings.append(f"Missing automation system: {system}")
                    
        # Security systems
        security = property_data.get('security_systems', {})
        if security.get('required') and not security.get('installed'):
            warnings.append("Required security system not installed")
            
        # Emergency response
        emergency = property_data.get('emergency_access', {})
        if emergency.get('response_time', 0) > 10:
            warnings.append(f"Long emergency response time: {emergency['response_time']} minutes")
            
        return warnings
        
    def _calculate_roi(self, property_data: Dict) -> float:
        """Calculate return on investment"""
        try:
            annual_income = property_data.get('projected_income', 0)
            purchase_price = property_data.get('purchase_price', 0)
            annual_expenses = property_data.get('projected_expenses', 0)
            
            if purchase_price == 0:
                return 0
                
            return (annual_income - annual_expenses) / purchase_price
            
        except Exception as e:
            self.logger.error(f"Error calculating ROI: {str(e)}")
            return 0.0
