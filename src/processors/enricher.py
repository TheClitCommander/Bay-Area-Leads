"""
Enriches property data with additional context and derived information
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import requests

class DataEnricher:
    """
    Enriches property data with:
    1. Derived metrics and indicators
    2. Geographic context
    3. Market context
    4. Historical trends
    5. Risk indicators
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Initialize geocoder
        self.geocoder = Nominatim(user_agent="midcoast_leads")
        
        # Configure enrichment sources
        self.sources = {
            'census': config.get('census_api_key'),
            'walkscore': config.get('walkscore_api_key'),
            'school_data': config.get('school_data_api_key')
        }
        
        # Load reference data
        self.reference_data = self._load_reference_data()

    def enrich_property(self, property_data: Dict) -> Dict:
        """
        Enrich a single property record with additional data
        """
        try:
            enriched = property_data.copy()
            
            # Add derived metrics
            enriched['derived_metrics'] = self._calculate_derived_metrics(property_data)
            
            # Add geographic context
            enriched['geographic_context'] = self._get_geographic_context(property_data)
            
            # Add market context
            enriched['market_context'] = self._get_market_context(property_data)
            
            # Add historical analysis
            enriched['historical_analysis'] = self._analyze_history(property_data)
            
            # Add risk indicators
            enriched['risk_indicators'] = self._calculate_risk_indicators(property_data)
            
            # Add metadata
            enriched['_enriched'] = True
            enriched['_enriched_at'] = datetime.now().isoformat()
            
            return enriched
            
        except Exception as e:
            self.logger.error(f"Error enriching property: {str(e)}")
            return property_data

    def enrich_batch(self, properties: List[Dict]) -> List[Dict]:
        """
        Enrich a batch of properties
        Also adds comparative metrics
        """
        try:
            # First pass: basic enrichment
            enriched = [
                self.enrich_property(prop)
                for prop in properties
            ]
            
            # Second pass: add comparative metrics
            df = pd.DataFrame(enriched)
            
            for prop in enriched:
                try:
                    prop['comparative_metrics'] = self._calculate_comparative_metrics(
                        prop, df
                    )
                except Exception as e:
                    self.logger.error(f"Error calculating comparative metrics: {str(e)}")
                    prop['comparative_metrics'] = {}
            
            return enriched
            
        except Exception as e:
            self.logger.error(f"Error in batch enrichment: {str(e)}")
            return properties

    def _calculate_derived_metrics(self, property_data: Dict) -> Dict:
        """Calculate derived metrics from property data"""
        try:
            metrics = {}
            
            # Value metrics
            assessment = property_data.get('assessment', {})
            if assessment:
                # Price per square foot
                if assessment.get('total_value') and property_data.get('square_feet'):
                    metrics['price_per_sqft'] = float(
                        assessment['total_value'] / property_data['square_feet']
                    )
                
                # Land value ratio
                if assessment.get('land_value') and assessment.get('total_value'):
                    metrics['land_value_ratio'] = float(
                        assessment['land_value'] / assessment['total_value']
                    )
            
            # Utilization metrics
            if property_data.get('lot_size') and property_data.get('square_feet'):
                metrics['floor_area_ratio'] = float(
                    property_data['square_feet'] / property_data['lot_size']
                )
            
            # Age and condition
            if property_data.get('year_built'):
                metrics['age'] = datetime.now().year - property_data['year_built']
                
                # Estimated remaining life
                typical_life = {
                    'single_family': 75,
                    'multi_family': 65,
                    'commercial': 50,
                    'industrial': 45
                }
                prop_type = property_data.get('property_type', 'single_family')
                life_expectancy = typical_life.get(prop_type, 60)
                
                metrics['estimated_remaining_life'] = max(
                    0, life_expectancy - metrics['age']
                )
            
            # Transaction metrics
            transactions = property_data.get('transactions', [])
            if transactions:
                # Average holding period
                holding_periods = []
                for i in range(len(transactions) - 1):
                    start = datetime.fromisoformat(transactions[i]['date'])
                    end = datetime.fromisoformat(transactions[i + 1]['date'])
                    holding_periods.append((end - start).days / 365)
                
                if holding_periods:
                    metrics['avg_holding_period'] = float(np.mean(holding_periods))
                
                # Price appreciation
                prices = [t['price'] for t in transactions if t.get('price')]
                if len(prices) > 1:
                    total_appreciation = (prices[-1] - prices[0]) / prices[0] * 100
                    years = (
                        datetime.fromisoformat(transactions[-1]['date']) -
                        datetime.fromisoformat(transactions[0]['date'])
                    ).days / 365
                    
                    metrics['total_appreciation'] = float(total_appreciation)
                    metrics['annual_appreciation'] = float(
                        total_appreciation / years
                    ) if years > 0 else 0
            
            # Permit and violation metrics
            permits = property_data.get('permits', [])
            if permits:
                metrics['total_improvements'] = sum(
                    p['estimated_cost'] for p in permits
                    if p.get('estimated_cost')
                )
                
                metrics['improvement_ratio'] = float(
                    metrics['total_improvements'] / assessment['total_value']
                ) if assessment.get('total_value') else 0
            
            violations = property_data.get('violations', [])
            if violations:
                metrics['violation_severity_score'] = self._calculate_violation_score(
                    violations
                )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating derived metrics: {str(e)}")
            return {}

    def _get_geographic_context(self, property_data: Dict) -> Dict:
        """Get geographic context for property"""
        try:
            context = {}
            
            # Get coordinates if not present
            coords = property_data.get('coordinates', {})
            if not coords:
                try:
                    location = self.geocoder.geocode(
                        f"{property_data.get('address')}, "
                        f"{property_data.get('city')}, "
                        f"{property_data.get('state')}"
                    )
                    if location:
                        coords = {
                            'latitude': location.latitude,
                            'longitude': location.longitude
                        }
                except Exception as e:
                    self.logger.warning(f"Geocoding failed: {str(e)}")
            
            if coords:
                # Get neighborhood data
                try:
                    context['neighborhood'] = self._get_neighborhood_data(coords)
                except Exception as e:
                    self.logger.warning(f"Error getting neighborhood data: {str(e)}")
                
                # Get nearby amenities
                try:
                    context['amenities'] = self._get_nearby_amenities(coords)
                except Exception as e:
                    self.logger.warning(f"Error getting amenities: {str(e)}")
                
                # Get school data
                try:
                    context['schools'] = self._get_school_data(coords)
                except Exception as e:
                    self.logger.warning(f"Error getting school data: {str(e)}")
                
                # Get walk score
                if self.sources.get('walkscore'):
                    try:
                        context['walk_score'] = self._get_walk_score(
                            coords,
                            property_data.get('address')
                        )
                    except Exception as e:
                        self.logger.warning(f"Error getting walk score: {str(e)}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting geographic context: {str(e)}")
            return {}

    def _get_market_context(self, property_data: Dict) -> Dict:
        """Get market context for property"""
        try:
            context = {}
            
            # Get local market trends
            if self.reference_data.get('market_trends'):
                context['market_trends'] = self._get_local_market_trends(
                    property_data
                )
            
            # Get comparable sales
            if property_data.get('assessment'):
                context['comparable_sales'] = self._get_comparable_sales(
                    property_data
                )
            
            # Get market indicators
            context['market_indicators'] = self._calculate_market_indicators(
                property_data
            )
            
            # Get investment metrics
            if property_data.get('transactions') or property_data.get('assessment'):
                context['investment_metrics'] = self._calculate_investment_metrics(
                    property_data
                )
            
            return context
            
        except Exception as e:
            self.logger.error(f"Error getting market context: {str(e)}")
            return {}

    def _analyze_history(self, property_data: Dict) -> Dict:
        """Analyze property history"""
        try:
            analysis = {}
            
            # Ownership history analysis
            if property_data.get('transactions'):
                analysis['ownership'] = self._analyze_ownership_history(
                    property_data['transactions']
                )
            
            # Value history analysis
            if property_data.get('assessment'):
                analysis['value'] = self._analyze_value_history(
                    property_data
                )
            
            # Improvement history analysis
            if property_data.get('permits'):
                analysis['improvements'] = self._analyze_improvement_history(
                    property_data['permits']
                )
            
            # Issue history analysis
            if property_data.get('violations'):
                analysis['issues'] = self._analyze_issue_history(
                    property_data['violations']
                )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing history: {str(e)}")
            return {}

    def _calculate_risk_indicators(self, property_data: Dict) -> Dict:
        """Calculate risk indicators"""
        try:
            indicators = {}
            
            # Property condition risks
            indicators['condition'] = self._assess_condition_risks(property_data)
            
            # Market risks
            indicators['market'] = self._assess_market_risks(property_data)
            
            # Financial risks
            indicators['financial'] = self._assess_financial_risks(property_data)
            
            # Legal risks
            indicators['legal'] = self._assess_legal_risks(property_data)
            
            # Calculate overall risk score
            risk_weights = {
                'condition': 0.3,
                'market': 0.3,
                'financial': 0.2,
                'legal': 0.2
            }
            
            total_score = 0
            valid_weights = 0
            
            for category, weight in risk_weights.items():
                if indicators[category].get('score') is not None:
                    total_score += indicators[category]['score'] * weight
                    valid_weights += weight
            
            if valid_weights > 0:
                indicators['overall_score'] = float(
                    total_score / valid_weights
                )
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error calculating risk indicators: {str(e)}")
            return {}

    def _calculate_comparative_metrics(self, property_data: Dict, df: pd.DataFrame) -> Dict:
        """Calculate comparative metrics against similar properties"""
        try:
            metrics = {}
            
            # Filter similar properties
            similar = df[
                (df['property_type'] == property_data.get('property_type')) &
                (df['property_id'] != property_data.get('property_id'))
            ]
            
            if len(similar) == 0:
                return metrics
            
            # Value comparisons
            if 'assessment' in property_data:
                value = property_data['assessment'].get('total_value')
                if value:
                    similar_values = similar['assessment'].apply(
                        lambda x: x.get('total_value')
                    ).dropna()
                    
                    metrics['value_percentile'] = float(
                        percentileofscore(similar_values, value)
                    )
                    
                    metrics['value_comparison'] = {
                        'average': float(similar_values.mean()),
                        'median': float(similar_values.median()),
                        'std_dev': float(similar_values.std())
                    }
            
            # Size comparisons
            if 'square_feet' in property_data:
                sqft = property_data['square_feet']
                similar_sqft = similar['square_feet'].dropna()
                
                metrics['size_percentile'] = float(
                    percentileofscore(similar_sqft, sqft)
                )
                
                metrics['size_comparison'] = {
                    'average': float(similar_sqft.mean()),
                    'median': float(similar_sqft.median()),
                    'std_dev': float(similar_sqft.std())
                }
            
            # Transaction comparisons
            if 'transactions' in property_data:
                metrics['transaction_comparison'] = self._compare_transactions(
                    property_data['transactions'],
                    similar
                )
            
            # Permit comparisons
            if 'permits' in property_data:
                metrics['permit_comparison'] = self._compare_permits(
                    property_data['permits'],
                    similar
                )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating comparative metrics: {str(e)}")
            return {}

    def _load_reference_data(self) -> Dict:
        """Load reference data for enrichment"""
        try:
            data = {}
            
            # Load market trends
            trends_file = self.config.get('market_trends_file')
            if trends_file:
                try:
                    data['market_trends'] = pd.read_csv(trends_file)
                except Exception as e:
                    self.logger.warning(f"Error loading market trends: {str(e)}")
            
            # Load neighborhood data
            neighborhood_file = self.config.get('neighborhood_file')
            if neighborhood_file:
                try:
                    data['neighborhoods'] = pd.read_csv(neighborhood_file)
                except Exception as e:
                    self.logger.warning(f"Error loading neighborhood data: {str(e)}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error loading reference data: {str(e)}")
            return {}
