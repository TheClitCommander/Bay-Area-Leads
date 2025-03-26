"""
Detects and scores investment opportunities in property data
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import IsolationForest

class OpportunityDetector:
    """
    Detects and scores investment opportunities
    Handles:
    1. Value opportunity detection
    2. Market timing analysis
    3. Property potential assessment
    4. Comparative advantage analysis
    5. Risk-adjusted scoring
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Configure scoring weights
        self.weights = {
            'value': 0.3,
            'growth': 0.2,
            'condition': 0.15,
            'location': 0.15,
            'market': 0.1,
            'risk': 0.1
        }
        
        # Update weights from config
        if 'scoring_weights' in config:
            self.weights.update(config['scoring_weights'])

    def detect_opportunities(self, properties: List[Dict]) -> List[Dict]:
        """
        Detect investment opportunities across properties
        """
        try:
            opportunities = []
            
            # Convert to dataframe for analysis
            df = pd.DataFrame(properties)
            
            # Calculate base scores
            value_scores = self._calculate_value_scores(df)
            growth_scores = self._calculate_growth_scores(df)
            condition_scores = self._calculate_condition_scores(df)
            location_scores = self._calculate_location_scores(df)
            market_scores = self._calculate_market_scores(df)
            risk_scores = self._calculate_risk_scores(df)
            
            # Combine scores
            for idx, prop in df.iterrows():
                try:
                    scores = {
                        'value_score': value_scores.get(prop['property_id'], 0),
                        'growth_score': growth_scores.get(prop['property_id'], 0),
                        'condition_score': condition_scores.get(prop['property_id'], 0),
                        'location_score': location_scores.get(prop['property_id'], 0),
                        'market_score': market_scores.get(prop['property_id'], 0),
                        'risk_score': risk_scores.get(prop['property_id'], 0)
                    }
                    
                    # Calculate weighted total score
                    total_score = sum(
                        scores[f"{k}_score"] * v
                        for k, v in self.weights.items()
                    )
                    
                    # Generate insights
                    insights = self._generate_insights(prop.to_dict(), scores)
                    
                    opportunities.append({
                        'property_id': prop['property_id'],
                        'scores': scores,
                        'total_score': float(total_score),
                        'insights': insights,
                        'opportunity_type': self._classify_opportunity(scores)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error processing property: {str(e)}")
                    continue
            
            # Sort by total score
            opportunities.sort(key=lambda x: x['total_score'], reverse=True)
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error detecting opportunities: {str(e)}")
            return []

    def analyze_market_timing(self, market_data: List[Dict]) -> Dict:
        """
        Analyze market timing factors
        """
        try:
            timing = {
                'market_cycle': self._analyze_market_cycle(market_data),
                'seasonal_factors': self._analyze_seasonal_factors(market_data),
                'price_trends': self._analyze_price_trends(market_data),
                'inventory_levels': self._analyze_inventory_levels(market_data),
                'market_conditions': self._analyze_market_conditions(market_data)
            }
            
            return timing
            
        except Exception as e:
            self.logger.error(f"Error analyzing market timing: {str(e)}")
            return {}

    def assess_property_potential(self, property_data: Dict) -> Dict:
        """
        Assess potential for property improvement and value addition
        """
        try:
            potential = {
                'improvement_potential': self._assess_improvement_potential(
                    property_data
                ),
                'development_potential': self._assess_development_potential(
                    property_data
                ),
                'income_potential': self._assess_income_potential(
                    property_data
                ),
                'value_add_opportunities': self._identify_value_add_opportunities(
                    property_data
                )
            }
            
            return potential
            
        except Exception as e:
            self.logger.error(f"Error assessing property potential: {str(e)}")
            return {}

    def analyze_comparative_advantage(self, 
                                   target_property: Dict,
                                   comparison_properties: List[Dict]) -> Dict:
        """
        Analyze comparative advantages against similar properties
        """
        try:
            advantages = {
                'price_advantages': self._analyze_price_advantages(
                    target_property,
                    comparison_properties
                ),
                'feature_advantages': self._analyze_feature_advantages(
                    target_property,
                    comparison_properties
                ),
                'location_advantages': self._analyze_location_advantages(
                    target_property,
                    comparison_properties
                ),
                'market_advantages': self._analyze_market_advantages(
                    target_property,
                    comparison_properties
                )
            }
            
            return advantages
            
        except Exception as e:
            self.logger.error(f"Error analyzing comparative advantage: {str(e)}")
            return {}

    def _calculate_value_scores(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate value opportunity scores"""
        try:
            scores = {}
            
            # Extract relevant metrics
            metrics = pd.DataFrame({
                'property_id': df['property_id'],
                'price_per_sqft': df.apply(
                    lambda x: (
                        x.get('assessment', {}).get('total_value', 0) /
                        x.get('square_feet', 1)
                    ),
                    axis=1
                ),
                'land_value_ratio': df.apply(
                    lambda x: (
                        x.get('assessment', {}).get('land_value', 0) /
                        x.get('assessment', {}).get('total_value', 1)
                    ),
                    axis=1
                )
            })
            
            # Normalize metrics
            scaler = MinMaxScaler()
            normalized = scaler.fit_transform(
                metrics[['price_per_sqft', 'land_value_ratio']]
            )
            
            # Calculate scores
            for i, prop_id in enumerate(metrics['property_id']):
                price_score = 1 - normalized[i, 0]  # Lower price is better
                land_score = normalized[i, 1]       # Higher land value ratio is better
                
                scores[prop_id] = float(
                    0.7 * price_score + 0.3 * land_score
                )
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error calculating value scores: {str(e)}")
            return {}

    def _calculate_growth_scores(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate growth potential scores"""
        try:
            scores = {}
            
            for idx, prop in df.iterrows():
                try:
                    # Calculate historical appreciation
                    transactions = prop.get('transactions', [])
                    if len(transactions) > 1:
                        first_price = transactions[0]['price']
                        last_price = transactions[-1]['price']
                        years = (
                            datetime.fromisoformat(transactions[-1]['date']) -
                            datetime.fromisoformat(transactions[0]['date'])
                        ).days / 365.25
                        
                        if years > 0:
                            annual_appreciation = (
                                (last_price / first_price) ** (1/years) - 1
                            )
                        else:
                            annual_appreciation = 0
                    else:
                        annual_appreciation = 0
                    
                    # Consider market factors
                    market_score = self._calculate_market_growth_score(prop)
                    
                    # Consider improvement potential
                    improvement_score = self._calculate_improvement_potential_score(prop)
                    
                    # Combine scores
                    scores[prop['property_id']] = float(
                        0.4 * annual_appreciation +
                        0.3 * market_score +
                        0.3 * improvement_score
                    )
                    
                except Exception as e:
                    self.logger.warning(f"Error calculating growth score: {str(e)}")
                    scores[prop['property_id']] = 0
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error calculating growth scores: {str(e)}")
            return {}

    def _calculate_condition_scores(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate property condition scores"""
        try:
            scores = {}
            
            for idx, prop in df.iterrows():
                try:
                    # Base score on age and improvements
                    age = datetime.now().year - prop.get('year_built', 1900)
                    age_score = max(0, 1 - (age / 100))  # Older properties score lower
                    
                    # Consider improvements
                    improvements = sum(
                        p.get('estimated_cost', 0)
                        for p in prop.get('permits', [])
                        if p.get('permit_type') in ['renovation', 'improvement']
                    )
                    
                    improvement_ratio = improvements / prop.get(
                        'assessment', {}
                    ).get('total_value', 1)
                    
                    improvement_score = min(1, improvement_ratio)
                    
                    # Consider violations
                    violations = prop.get('violations', [])
                    violation_score = max(
                        0,
                        1 - (len(violations) * 0.1)
                    )
                    
                    # Combine scores
                    scores[prop['property_id']] = float(
                        0.4 * age_score +
                        0.4 * improvement_score +
                        0.2 * violation_score
                    )
                    
                except Exception as e:
                    self.logger.warning(f"Error calculating condition score: {str(e)}")
                    scores[prop['property_id']] = 0
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error calculating condition scores: {str(e)}")
            return {}

    def _calculate_location_scores(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate location quality scores"""
        try:
            scores = {}
            
            for idx, prop in df.iterrows():
                try:
                    # Get location factors
                    location_data = prop.get('geographic_context', {})
                    
                    factors = {
                        'walk_score': location_data.get('walk_score', 0) / 100,
                        'school_score': self._calculate_school_score(
                            location_data.get('schools', [])
                        ),
                        'amenity_score': self._calculate_amenity_score(
                            location_data.get('amenities', {})
                        ),
                        'neighborhood_score': self._calculate_neighborhood_score(
                            location_data.get('neighborhood', {})
                        )
                    }
                    
                    # Combine scores
                    scores[prop['property_id']] = float(
                        0.3 * factors['walk_score'] +
                        0.3 * factors['school_score'] +
                        0.2 * factors['amenity_score'] +
                        0.2 * factors['neighborhood_score']
                    )
                    
                except Exception as e:
                    self.logger.warning(f"Error calculating location score: {str(e)}")
                    scores[prop['property_id']] = 0
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error calculating location scores: {str(e)}")
            return {}

    def _calculate_market_scores(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate market condition scores"""
        try:
            scores = {}
            
            for idx, prop in df.iterrows():
                try:
                    market_data = prop.get('market_context', {})
                    
                    factors = {
                        'demand_score': self._calculate_demand_score(market_data),
                        'supply_score': self._calculate_supply_score(market_data),
                        'price_trend_score': self._calculate_price_trend_score(market_data),
                        'market_activity_score': self._calculate_market_activity_score(
                            market_data
                        )
                    }
                    
                    # Combine scores
                    scores[prop['property_id']] = float(
                        0.3 * factors['demand_score'] +
                        0.2 * factors['supply_score'] +
                        0.3 * factors['price_trend_score'] +
                        0.2 * factors['market_activity_score']
                    )
                    
                except Exception as e:
                    self.logger.warning(f"Error calculating market score: {str(e)}")
                    scores[prop['property_id']] = 0
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error calculating market scores: {str(e)}")
            return {}

    def _calculate_risk_scores(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate risk-adjusted scores"""
        try:
            scores = {}
            
            for idx, prop in df.iterrows():
                try:
                    risk_factors = prop.get('risk_indicators', {})
                    
                    factors = {
                        'market_risk': self._calculate_market_risk(risk_factors),
                        'property_risk': self._calculate_property_risk(risk_factors),
                        'financial_risk': self._calculate_financial_risk(risk_factors),
                        'legal_risk': self._calculate_legal_risk(risk_factors)
                    }
                    
                    # Calculate overall risk score (lower is better)
                    risk_score = (
                        0.3 * factors['market_risk'] +
                        0.3 * factors['property_risk'] +
                        0.2 * factors['financial_risk'] +
                        0.2 * factors['legal_risk']
                    )
                    
                    # Convert to 0-1 scale where 1 is lowest risk
                    scores[prop['property_id']] = float(1 - risk_score)
                    
                except Exception as e:
                    self.logger.warning(f"Error calculating risk score: {str(e)}")
                    scores[prop['property_id']] = 0
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error calculating risk scores: {str(e)}")
            return {}

    def _generate_insights(self, property_data: Dict, scores: Dict) -> List[Dict]:
        """Generate insights based on scores and property data"""
        try:
            insights = []
            
            # Value insights
            if scores['value_score'] > 0.7:
                insights.append({
                    'type': 'value',
                    'level': 'high',
                    'message': 'Property shows strong value opportunity'
                })
            
            # Growth insights
            if scores['growth_score'] > 0.7:
                insights.append({
                    'type': 'growth',
                    'level': 'high',
                    'message': 'High potential for appreciation'
                })
            
            # Condition insights
            if scores['condition_score'] < 0.3:
                insights.append({
                    'type': 'condition',
                    'level': 'opportunity',
                    'message': 'Property may benefit from improvements'
                })
            
            # Location insights
            if scores['location_score'] > 0.7:
                insights.append({
                    'type': 'location',
                    'level': 'positive',
                    'message': 'Excellent location characteristics'
                })
            
            # Market insights
            if scores['market_score'] > 0.7:
                insights.append({
                    'type': 'market',
                    'level': 'favorable',
                    'message': 'Strong market conditions'
                })
            
            # Risk insights
            if scores['risk_score'] < 0.3:
                insights.append({
                    'type': 'risk',
                    'level': 'warning',
                    'message': 'Higher risk factors present'
                })
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            return []

    def _classify_opportunity(self, scores: Dict) -> str:
        """Classify the type of investment opportunity"""
        try:
            # Define thresholds
            high_threshold = 0.7
            low_threshold = 0.3
            
            # Check for specific opportunity types
            if scores['value_score'] > high_threshold:
                if scores['condition_score'] < low_threshold:
                    return 'value_add'
                else:
                    return 'value_buy'
            
            if scores['growth_score'] > high_threshold:
                if scores['market_score'] > high_threshold:
                    return 'growth_market'
                else:
                    return 'development_potential'
            
            if scores['location_score'] > high_threshold:
                if scores['condition_score'] < low_threshold:
                    return 'location_improvement'
                else:
                    return 'premium_location'
            
            if all(score > 0.5 for score in scores.values()):
                return 'balanced_opportunity'
            
            return 'standard'
            
        except Exception as e:
            self.logger.error(f"Error classifying opportunity: {str(e)}")
            return 'unknown'
