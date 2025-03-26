"""
Advanced specialized validation rules
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime
import logging
import numpy as np
from scipy import stats
import pandas as pd
from geopy.distance import geodesic
from shapely.geometry import Point, Polygon, MultiPolygon
import geopandas as gpd

class MarketTrend(Enum):
    RISING = 'rising'
    STABLE = 'stable'
    DECLINING = 'declining'

class PropertyCondition(Enum):
    EXCELLENT = 'excellent'
    GOOD = 'good'
    FAIR = 'fair'
    POOR = 'poor'

@dataclass
class MarketAnalysis:
    trend: MarketTrend
    confidence: float
    comparable_sales: List[Dict]
    price_per_sqft: float
    days_on_market: int

class AdvancedRules:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
    def validate_market_conditions(self, property_data: Dict, market_data: List[Dict]) -> List[str]:
        """Validate property against market conditions"""
        warnings = []
        
        try:
            analysis = self._analyze_market(property_data, market_data)
            
            # Check price against market trend
            if analysis.trend == MarketTrend.RISING and property_data['price_per_sqft'] < analysis.price_per_sqft * 0.8:
                warnings.append(f"Property price ({property_data['price_per_sqft']}/sqft) significantly below market average ({analysis.price_per_sqft}/sqft) in rising market")
                
            elif analysis.trend == MarketTrend.DECLINING and property_data['price_per_sqft'] > analysis.price_per_sqft * 1.2:
                warnings.append(f"Property price ({property_data['price_per_sqft']}/sqft) significantly above market average ({analysis.price_per_sqft}/sqft) in declining market")
                
            # Check days on market
            if analysis.days_on_market > 180:
                warnings.append(f"Property has been on market for {analysis.days_on_market} days, significantly above average")
                
        except Exception as e:
            self.logger.error(f"Error in market validation: {str(e)}")
            
        return warnings
        
    def validate_flood_risk(self, property_data: Dict, flood_data: Dict) -> List[str]:
        """Validate flood risk and insurance requirements"""
        warnings = []
        
        try:
            flood_zone = flood_data.get('zone')
            base_flood_elevation = flood_data.get('base_elevation')
            property_elevation = property_data.get('elevation')
            
            if flood_zone in ['A', 'AE', 'V', 'VE']:
                warnings.append(f"Property in high-risk flood zone {flood_zone}")
                
                if property_elevation and base_flood_elevation:
                    if property_elevation < base_flood_elevation:
                        warnings.append(f"Property elevation ({property_elevation}ft) below base flood elevation ({base_flood_elevation}ft)")
                        
            if flood_data.get('insurance_required'):
                warnings.append("Flood insurance required for this property")
                
        except Exception as e:
            self.logger.error(f"Error in flood risk validation: {str(e)}")
            
        return warnings
        
    def validate_historical_significance(self, property_data: Dict, historical_data: Dict) -> List[str]:
        """Validate historical property requirements"""
        warnings = []
        
        try:
            if historical_data.get('is_historic'):
                # Check for historical registry requirements
                if not property_data.get('historical_registry_number'):
                    warnings.append("Missing historical registry number for historic property")
                    
                # Check for preservation requirements
                modifications = property_data.get('modifications', [])
                for mod in modifications:
                    if not mod.get('preservation_approved'):
                        warnings.append(f"Unapproved modification: {mod.get('description')}")
                        
                # Check for historical features
                required_features = historical_data.get('required_features', [])
                current_features = property_data.get('features', [])
                
                for feature in required_features:
                    if feature not in current_features:
                        warnings.append(f"Missing required historical feature: {feature}")
                        
        except Exception as e:
            self.logger.error(f"Error in historical validation: {str(e)}")
            
        return warnings
        
    def validate_energy_efficiency(self, property_data: Dict) -> List[str]:
        """Validate energy efficiency requirements"""
        warnings = []
        
        try:
            # Check energy rating
            energy_rating = property_data.get('energy_rating')
            if energy_rating:
                if energy_rating < 50:
                    warnings.append(f"Low energy efficiency rating: {energy_rating}")
                    
            # Check insulation
            insulation = property_data.get('insulation_rating')
            if insulation and insulation < 'R-30':
                warnings.append(f"Insufficient insulation rating: {insulation}")
                
            # Check windows
            windows = property_data.get('window_type')
            if windows and windows != 'double_pane':
                warnings.append("Non-energy efficient windows")
                
            # Check HVAC
            hvac_age = property_data.get('hvac_age')
            if hvac_age and hvac_age > 15:
                warnings.append(f"HVAC system age ({hvac_age} years) may affect efficiency")
                
        except Exception as e:
            self.logger.error(f"Error in energy efficiency validation: {str(e)}")
            
        return warnings
        
    def validate_accessibility(self, property_data: Dict) -> List[str]:
        """Validate accessibility requirements"""
        warnings = []
        
        try:
            if property_data.get('requires_accessibility'):
                # Check doorway widths
                doorways = property_data.get('doorway_widths', {})
                for location, width in doorways.items():
                    if width < 32:
                        warnings.append(f"Insufficient doorway width at {location}: {width} inches")
                        
                # Check ramps
                ramps = property_data.get('ramps', [])
                for ramp in ramps:
                    if ramp['slope'] > 1/12:
                        warnings.append(f"Ramp slope too steep: {ramp['location']}")
                        
                # Check bathroom accessibility
                bathrooms = property_data.get('bathrooms', [])
                accessible_bath = False
                for bath in bathrooms:
                    if bath.get('accessible'):
                        accessible_bath = True
                        break
                if not accessible_bath:
                    warnings.append("No accessible bathroom found")
                    
        except Exception as e:
            self.logger.error(f"Error in accessibility validation: {str(e)}")
            
        return warnings
        
    def validate_natural_hazards(self, property_data: Dict, hazard_data: Dict) -> List[str]:
        """Validate natural hazard risks"""
        warnings = []
        
        try:
            # Check earthquake risk
            eq_risk = hazard_data.get('earthquake_risk')
            if eq_risk and eq_risk > 0.3:
                warnings.append(f"High earthquake risk: {eq_risk}")
                
                # Check seismic retrofitting
                if not property_data.get('seismic_retrofitting'):
                    warnings.append("Seismic retrofitting recommended")
                    
            # Check wildfire risk
            fire_risk = hazard_data.get('wildfire_risk')
            if fire_risk and fire_risk > 0.3:
                warnings.append(f"High wildfire risk: {fire_risk}")
                
                # Check defensible space
                if not property_data.get('defensible_space'):
                    warnings.append("Defensible space requirements not met")
                    
            # Check landslide risk
            landslide_risk = hazard_data.get('landslide_risk')
            if landslide_risk and landslide_risk > 0.3:
                warnings.append(f"High landslide risk: {landslide_risk}")
                
                # Check slope stability
                if not property_data.get('slope_stability_assessed'):
                    warnings.append("Slope stability assessment recommended")
                    
        except Exception as e:
            self.logger.error(f"Error in natural hazard validation: {str(e)}")
            
        return warnings
        
    def validate_infrastructure(self, property_data: Dict, infrastructure_data: Dict) -> List[str]:
        """Validate infrastructure requirements"""
        warnings = []
        
        try:
            # Check utility connections
            utilities = infrastructure_data.get('utilities', {})
            for utility, status in utilities.items():
                if status.get('condition') == 'poor':
                    warnings.append(f"Poor {utility} infrastructure condition")
                if not status.get('connected'):
                    warnings.append(f"Property not connected to {utility}")
                    
            # Check road access
            road_access = infrastructure_data.get('road_access', {})
            if road_access.get('condition') == 'poor':
                warnings.append("Poor road access condition")
            if not road_access.get('maintained'):
                warnings.append("Road not maintained by municipality")
                
            # Check internet connectivity
            internet = infrastructure_data.get('internet', {})
            if internet.get('speed', 0) < 25:
                warnings.append(f"Low internet speed available: {internet.get('speed')}Mbps")
                
        except Exception as e:
            self.logger.error(f"Error in infrastructure validation: {str(e)}")
            
        return warnings
        
    def _analyze_market(self, property_data: Dict, market_data: List[Dict]) -> MarketAnalysis:
        """Analyze market conditions"""
        try:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(market_data)
            
            # Calculate price trends
            df['price_change'] = df['sale_price'].pct_change()
            trend_mean = df['price_change'].mean()
            
            # Determine market trend
            if trend_mean > 0.05:
                trend = MarketTrend.RISING
            elif trend_mean < -0.05:
                trend = MarketTrend.DECLINING
            else:
                trend = MarketTrend.STABLE
                
            # Calculate confidence
            confidence = 1 - stats.sem(df['price_change'])
            
            # Find comparable sales
            comparable_sales = self._find_comparables(property_data, df)
            
            # Calculate metrics
            price_per_sqft = df['price_per_sqft'].mean()
            days_on_market = df['days_on_market'].mean()
            
            return MarketAnalysis(
                trend=trend,
                confidence=confidence,
                comparable_sales=comparable_sales,
                price_per_sqft=price_per_sqft,
                days_on_market=days_on_market
            )
            
        except Exception as e:
            self.logger.error(f"Error in market analysis: {str(e)}")
            raise
            
    def _find_comparables(self, property_data: Dict, market_df: pd.DataFrame) -> List[Dict]:
        """Find comparable properties"""
        try:
            # Filter by similar properties
            comparables = market_df[
                (market_df['square_feet'].between(
                    property_data['square_feet'] * 0.8,
                    property_data['square_feet'] * 1.2
                )) &
                (market_df['bedrooms'] == property_data['bedrooms']) &
                (market_df['property_type'] == property_data['property_type'])
            ]
            
            # Sort by similarity score
            comparables['similarity_score'] = comparables.apply(
                lambda x: self._calculate_similarity(property_data, x),
                axis=1
            )
            
            comparables = comparables.sort_values('similarity_score', ascending=False)
            
            return comparables.head(5).to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Error finding comparables: {str(e)}")
            return []
            
    def _calculate_similarity(self, property_data: Dict, comparable: pd.Series) -> float:
        """Calculate similarity score between properties"""
        try:
            # Calculate distance score
            distance = geodesic(
                (property_data['latitude'], property_data['longitude']),
                (comparable['latitude'], comparable['longitude'])
            ).miles
            distance_score = 1 / (1 + distance)
            
            # Calculate age difference score
            age_diff = abs(property_data['year_built'] - comparable['year_built'])
            age_score = 1 / (1 + age_diff/10)
            
            # Calculate condition score
            condition_diff = abs(
                PropertyCondition[property_data['condition']].value -
                PropertyCondition[comparable['condition']].value
            )
            condition_score = 1 / (1 + condition_diff)
            
            # Weighted average
            return (
                0.4 * distance_score +
                0.3 * age_score +
                0.3 * condition_score
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
