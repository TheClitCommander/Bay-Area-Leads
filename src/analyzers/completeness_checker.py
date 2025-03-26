"""
Checks data completeness for accurate scoring
"""
import logging
from typing import Dict, List, Set
from datetime import datetime

class CompletenessChecker:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Required fields for each occupation type
        self.occupation_requirements = {
            "landlord": {
                "critical": {
                    "property_data": ["owner_name", "property_type", "total_value"],
                    "property_use": ["rental_status", "unit_count"],
                    "tax_data": ["homestead_status"]
                },
                "important": {
                    "deed_data": ["ownership_history"],
                    "utility_data": ["usage_pattern"],
                    "permit_data": ["rental_permits"]
                }
            },
            "business_owner": {
                "critical": {
                    "property_data": ["owner_name", "property_type"],
                    "business_data": ["business_registrations", "licenses"]
                },
                "important": {
                    "tax_data": ["property_use_code"],
                    "deed_data": ["business_entities"],
                    "permit_data": ["business_permits"]
                }
            },
            "real_estate_investor": {
                "critical": {
                    "property_data": ["owner_name", "total_value"],
                    "deed_data": ["sale_history", "ownership_history"],
                    "tax_data": ["assessment_history"]
                },
                "important": {
                    "property_use": ["occupancy_status"],
                    "market_data": ["area_trends"],
                    "gis_data": ["zoning"]
                }
            },
            "high_net_worth": {
                "critical": {
                    "property_data": ["total_value", "property_type"],
                    "gis_data": ["waterfront_status", "lot_size"],
                    "tax_data": ["assessment_value"]
                },
                "important": {
                    "deed_data": ["sale_price"],
                    "property_use": ["improvements"],
                    "market_data": ["neighborhood_stats"]
                }
            },
            "distressed_owner": {
                "critical": {
                    "tax_data": ["delinquent_amount", "payment_status"],
                    "property_data": ["owner_name", "total_value"],
                    "lien_data": ["active_liens"]
                },
                "important": {
                    "utility_data": ["payment_status"],
                    "foreclosure_data": ["notices"],
                    "deed_data": ["recent_activity"]
                }
            }
        }

    def check_completeness(self, property_data: Dict, occupation_types: List[str] = None) -> Dict:
        """
        Check data completeness for specified occupation types
        
        Args:
            property_data: All collected data for a property
            occupation_types: List of occupation types to check, or None for all
            
        Returns:
            Dictionary with completeness scores and missing fields
        """
        try:
            results = {}
            
            # If no specific types requested, check all
            if not occupation_types:
                occupation_types = list(self.occupation_requirements.keys())
            
            for occupation in occupation_types:
                if occupation not in self.occupation_requirements:
                    continue
                
                requirements = self.occupation_requirements[occupation]
                
                # Check critical fields
                critical_score, critical_missing = self._check_field_set(
                    property_data, 
                    requirements["critical"]
                )
                
                # Check important fields
                important_score, important_missing = self._check_field_set(
                    property_data, 
                    requirements["important"]
                )
                
                # Calculate overall completeness
                overall_score = (critical_score * 0.7) + (important_score * 0.3)
                
                results[occupation] = {
                    "completeness_score": overall_score,
                    "critical_score": critical_score,
                    "important_score": important_score,
                    "missing_critical": critical_missing,
                    "missing_important": important_missing,
                    "can_score": critical_score >= 0.8,  # Need 80% of critical data
                    "confidence_level": self._calculate_confidence(
                        critical_score, 
                        important_score
                    )
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error checking completeness: {str(e)}")
            return {}
    
    def _check_field_set(self, data: Dict, required_fields: Dict) -> tuple:
        """Check presence of a set of required fields"""
        total_fields = 0
        found_fields = 0
        missing_fields = {}
        
        for category, fields in required_fields.items():
            total_fields += len(fields)
            category_data = data.get(category, {})
            
            missing_in_category = []
            for field in fields:
                if category_data.get(field):
                    found_fields += 1
                else:
                    missing_in_category.append(field)
            
            if missing_in_category:
                missing_fields[category] = missing_in_category
        
        score = found_fields / total_fields if total_fields > 0 else 0
        return score, missing_fields
    
    def _calculate_confidence(self, critical_score: float, important_score: float) -> str:
        """Calculate confidence level based on scores"""
        if critical_score >= 0.9 and important_score >= 0.8:
            return "High"
        elif critical_score >= 0.8 and important_score >= 0.6:
            return "Medium"
        elif critical_score >= 0.8:
            return "Low"
        else:
            return "Insufficient"
    
    def get_required_sources(self, occupation_type: str) -> Set[str]:
        """Get required data sources for an occupation type"""
        try:
            if occupation_type not in self.occupation_requirements:
                return set()
            
            sources = set()
            requirements = self.occupation_requirements[occupation_type]
            
            # Add all categories from both critical and important
            for importance in ["critical", "important"]:
                for category in requirements[importance].keys():
                    sources.add(category)
            
            return sources
            
        except Exception as e:
            self.logger.error(f"Error getting required sources: {str(e)}")
            return set()
