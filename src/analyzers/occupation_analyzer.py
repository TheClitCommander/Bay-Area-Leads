"""
Analyzer for scoring properties based on owner occupation
"""
import logging
from typing import Dict, List
from datetime import datetime
from ..models.base import get_db

class OccupationAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Occupation scoring criteria
        self.occupation_scores = {
            "landlord": {
                "indicators": {
                    "multiple_properties": {"weight": 30, "min_count": 2},
                    "rental_registration": {"weight": 25},
                    "multi_family_property": {"weight": 20},
                    "non_homestead": {"weight": 15},
                    "business_entity_owner": {"weight": 10}
                },
                "minimum_score": 40
            },
            "business_owner": {
                "indicators": {
                    "business_registration": {"weight": 30},
                    "commercial_property": {"weight": 25},
                    "professional_license": {"weight": 20},
                    "dba_record": {"weight": 15},
                    "ucc_filings": {"weight": 10}
                },
                "minimum_score": 30
            },
            "real_estate_investor": {
                "indicators": {
                    "frequent_transactions": {"weight": 30, "timeframe_months": 24},
                    "multiple_properties": {"weight": 25, "min_count": 3},
                    "non_owner_occupied": {"weight": 20},
                    "llc_ownership": {"weight": 15},
                    "high_value_properties": {"weight": 10}
                },
                "minimum_score": 35
            },
            "high_net_worth": {
                "indicators": {
                    "property_value": {"weight": 30, "threshold": 750000},
                    "multiple_properties": {"weight": 25, "min_count": 2},
                    "waterfront_location": {"weight": 20},
                    "recent_purchase": {"weight": 15, "months": 36},
                    "business_ownership": {"weight": 10}
                },
                "minimum_score": 45
            },
            "distressed_owner": {
                "indicators": {
                    "tax_delinquent": {"weight": 30, "min_amount": 1000},
                    "foreclosure_notice": {"weight": 25},
                    "tax_liens": {"weight": 20},
                    "utility_arrears": {"weight": 15},
                    "vacancy": {"weight": 10}
                },
                "minimum_score": 25
            }
        }
    
    def analyze_property(self, property_data: Dict) -> Dict[str, Dict]:
        """
        Analyze property and owner data for occupation matches
        
        Args:
            property_data: Combined data from all collectors
            
        Returns:
            Dictionary of occupation scores and confidence levels
        """
        try:
            results = {}
            
            for occupation, criteria in self.occupation_scores.items():
                score = 0
                indicators_met = []
                
                for indicator, specs in criteria["indicators"].items():
                    if self._check_indicator(indicator, specs, property_data):
                        score += specs["weight"]
                        indicators_met.append(indicator)
                
                confidence = (score / 100) * 100  # Convert to percentage
                
                if score >= criteria["minimum_score"]:
                    results[occupation] = {
                        "score": score,
                        "confidence": confidence,
                        "indicators_met": indicators_met
                    }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing property: {str(e)}")
            return {}
    
    def _check_indicator(self, indicator: str, specs: Dict, data: Dict) -> bool:
        """Check if a specific indicator is met"""
        try:
            if indicator == "multiple_properties":
                return len(data.get("owned_properties", [])) >= specs.get("min_count", 2)
                
            elif indicator == "rental_registration":
                return data.get("property_use", {}).get("rental_status", {}).get("is_rental", False)
                
            elif indicator == "multi_family_property":
                return data.get("property_type") == "Multi Family"
                
            elif indicator == "non_homestead":
                return not data.get("property_use", {}).get("homestead_status", {}).get("has_homestead", True)
                
            elif indicator == "business_entity_owner":
                return "LLC" in data.get("owner_name", "") or "INC" in data.get("owner_name", "").upper()
                
            elif indicator == "commercial_property":
                return data.get("property_type") == "Commercial"
                
            elif indicator == "professional_license":
                return bool(data.get("business_data", {}).get("professional_licenses"))
                
            elif indicator == "frequent_transactions":
                transactions = data.get("deed_history", [])
                if transactions:
                    recent_count = sum(1 for t in transactions 
                                     if (datetime.now() - datetime.strptime(t["date"], "%Y-%m-%d")).days <= specs["timeframe_months"] * 30)
                    return recent_count >= 2
                return False
                
            elif indicator == "high_value_properties":
                return data.get("total_value", 0) >= 500000
                
            elif indicator == "tax_delinquent":
                return data.get("delinquent_amount", 0) >= specs.get("min_amount", 0)
                
            elif indicator == "foreclosure_notice":
                return bool(data.get("foreclosure_data", {}).get("notices", []))
                
            elif indicator == "waterfront_location":
                return "Waterfront" in data.get("property_features", [])
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking indicator {indicator}: {str(e)}")
            return False
