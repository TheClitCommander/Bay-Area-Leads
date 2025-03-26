"""
Analyzes investment patterns and opportunities in property data
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.ensemble import RandomForestRegressor

class InvestmentAnalyzer:
    """
    Analyzes investment patterns and opportunities
    Handles:
    1. Investment pattern detection
    2. ROI analysis
    3. Market forecasting
    4. Opportunity scoring
    5. Risk assessment
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Configure analysis parameters
        self.params = {
            'min_data_points': 5,      # Minimum points for trend analysis
            'forecast_horizon': 12,     # Months to forecast
            'confidence_level': 0.95,   # For prediction intervals
            'min_roi': 0.05            # Minimum ROI to consider
        }
        
        # Update from config
        if 'analysis_params' in config:
            self.params.update(config['analysis_params'])

    def analyze_investment_patterns(self, properties: List[Dict]) -> Dict:
        """
        Analyze investment patterns across properties
        """
        try:
            patterns = {
                'buyer_patterns': self._analyze_buyer_patterns(properties),
                'value_patterns': self._analyze_value_patterns(properties),
                'improvement_patterns': self._analyze_improvement_patterns(properties),
                'holding_patterns': self._analyze_holding_patterns(properties),
                'geographic_patterns': self._analyze_geographic_patterns(properties)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing investment patterns: {str(e)}")
            return {}

    def analyze_roi(self, property_data: Dict, scenario: str = 'base') -> Dict:
        """
        Analyze potential ROI for different investment scenarios
        """
        try:
            # Get base property value
            current_value = property_data.get('assessment', {}).get('total_value')
            if not current_value:
                return {}
            
            # Define scenarios
            scenarios = {
                'base': {
                    'holding_period': 5,    # years
                    'improvements': 0,
                    'appreciation_rate': 0.03
                },
                'improve': {
                    'holding_period': 2,
                    'improvements': current_value * 0.15,
                    'appreciation_rate': 0.04
                },
                'long_term': {
                    'holding_period': 10,
                    'improvements': current_value * 0.05,
                    'appreciation_rate': 0.03
                }
            }
            
            # Calculate ROI for specified scenario
            scenario_params = scenarios.get(scenario, scenarios['base'])
            
            roi_analysis = self._calculate_roi(
                property_data,
                scenario_params
            )
            
            return roi_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing ROI: {str(e)}")
            return {}

    def forecast_market_trends(self, 
                             historical_data: List[Dict],
                             forecast_type: str = 'value') -> Dict:
        """
        Forecast market trends using historical data
        """
        try:
            # Convert to dataframe
            df = pd.DataFrame(historical_data)
            
            if len(df) < self.params['min_data_points']:
                return {}
            
            # Prepare data based on forecast type
            if forecast_type == 'value':
                y = df['assessment'].apply(lambda x: x.get('total_value'))
            elif forecast_type == 'price':
                y = df['transactions'].apply(
                    lambda x: x[-1]['price'] if x else None
                )
            else:
                return {}
            
            # Create time features
            X = self._create_time_features(df)
            
            # Generate forecast
            forecast = self._generate_forecast(X, y)
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"Error forecasting trends: {str(e)}")
            return {}

    def score_opportunities(self, properties: List[Dict]) -> List[Dict]:
        """
        Score investment opportunities across properties
        """
        try:
            scored_properties = []
            
            for prop in properties:
                try:
                    scores = {
                        'value_score': self._calculate_value_score(prop),
                        'growth_score': self._calculate_growth_score(prop),
                        'risk_score': self._calculate_risk_score(prop),
                        'opportunity_score': self._calculate_opportunity_score(prop)
                    }
                    
                    scored_properties.append({
                        'property_id': prop.get('property_id'),
                        'scores': scores,
                        'insights': self._generate_insights(prop, scores)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error scoring property: {str(e)}")
                    continue
            
            return scored_properties
            
        except Exception as e:
            self.logger.error(f"Error scoring opportunities: {str(e)}")
            return []

    def _analyze_buyer_patterns(self, properties: List[Dict]) -> Dict:
        """Analyze patterns in buyer behavior"""
        try:
            # Extract all transactions
            transactions = []
            for prop in properties:
                for trans in prop.get('transactions', []):
                    trans['property_id'] = prop.get('property_id')
                    trans['property_type'] = prop.get('property_type')
                    transactions.append(trans)
            
            if not transactions:
                return {}
            
            df = pd.DataFrame(transactions)
            
            # Analyze buyer frequency
            buyer_stats = df.groupby('buyer').agg({
                'price': ['count', 'mean', 'sum'],
                'property_id': 'nunique',
                'property_type': lambda x: list(set(x))
            })
            
            # Identify buyer patterns
            patterns = {
                'frequent_buyers': [
                    {
                        'buyer': buyer,
                        'transactions': int(stats[('price', 'count')]),
                        'avg_price': float(stats[('price', 'mean')]),
                        'total_investment': float(stats[('price', 'sum')]),
                        'unique_properties': int(stats[('property_id', 'nunique')]),
                        'property_types': stats[('property_type', 'lambda')]
                    }
                    for buyer, stats in buyer_stats.iterrows()
                    if stats[('price', 'count')] > 1
                ],
                'buyer_categories': self._categorize_buyers(buyer_stats)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing buyer patterns: {str(e)}")
            return {}

    def _analyze_value_patterns(self, properties: List[Dict]) -> Dict:
        """Analyze patterns in property values"""
        try:
            # Extract value data
            value_data = []
            for prop in properties:
                assessment = prop.get('assessment', {})
                if assessment:
                    value_data.append({
                        'property_id': prop.get('property_id'),
                        'property_type': prop.get('property_type'),
                        'total_value': assessment.get('total_value'),
                        'land_value': assessment.get('land_value'),
                        'building_value': assessment.get('building_value'),
                        'year_built': prop.get('year_built'),
                        'square_feet': prop.get('square_feet')
                    })
            
            if not value_data:
                return {}
            
            df = pd.DataFrame(value_data)
            
            # Calculate value metrics
            df['price_per_sqft'] = df['total_value'] / df['square_feet']
            df['land_value_ratio'] = df['land_value'] / df['total_value']
            
            # Analyze by property type
            type_analysis = {}
            for prop_type in df['property_type'].unique():
                type_df = df[df['property_type'] == prop_type]
                
                type_analysis[prop_type] = {
                    'value_distribution': {
                        'mean': float(type_df['total_value'].mean()),
                        'median': float(type_df['total_value'].median()),
                        'std': float(type_df['total_value'].std())
                    },
                    'price_per_sqft': {
                        'mean': float(type_df['price_per_sqft'].mean()),
                        'median': float(type_df['price_per_sqft'].median()),
                        'std': float(type_df['price_per_sqft'].std())
                    },
                    'land_value_ratio': {
                        'mean': float(type_df['land_value_ratio'].mean()),
                        'median': float(type_df['land_value_ratio'].median()),
                        'std': float(type_df['land_value_ratio'].std())
                    }
                }
            
            return {
                'by_type': type_analysis,
                'value_segments': self._analyze_value_segments(df)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing value patterns: {str(e)}")
            return {}

    def _analyze_improvement_patterns(self, properties: List[Dict]) -> Dict:
        """Analyze patterns in property improvements"""
        try:
            # Extract permit data
            permits = []
            for prop in properties:
                for permit in prop.get('permits', []):
                    permit['property_id'] = prop.get('property_id')
                    permit['property_type'] = prop.get('property_type')
                    permit['total_value'] = prop.get('assessment', {}).get('total_value')
                    permits.append(permit)
            
            if not permits:
                return {}
            
            df = pd.DataFrame(permits)
            
            # Calculate improvement metrics
            df['improvement_ratio'] = df['estimated_cost'] / df['total_value']
            
            # Analyze by permit type
            type_analysis = df.groupby('permit_type').agg({
                'estimated_cost': ['count', 'mean', 'sum'],
                'improvement_ratio': 'mean'
            })
            
            patterns = {
                'by_type': {
                    permit_type: {
                        'count': int(stats[('estimated_cost', 'count')]),
                        'avg_cost': float(stats[('estimated_cost', 'mean')]),
                        'total_cost': float(stats[('estimated_cost', 'sum')]),
                        'avg_improvement_ratio': float(
                            stats[('improvement_ratio', 'mean')]
                        )
                    }
                    for permit_type, stats in type_analysis.iterrows()
                },
                'improvement_trends': self._analyze_improvement_trends(df)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing improvement patterns: {str(e)}")
            return {}

    def _analyze_holding_patterns(self, properties: List[Dict]) -> Dict:
        """Analyze property holding patterns"""
        try:
            # Calculate holding periods
            holding_periods = []
            for prop in properties:
                transactions = prop.get('transactions', [])
                if len(transactions) > 1:
                    for i in range(len(transactions) - 1):
                        period = {
                            'property_id': prop.get('property_id'),
                            'property_type': prop.get('property_type'),
                            'owner': transactions[i]['buyer'],
                            'purchase_price': transactions[i]['price'],
                            'sale_price': transactions[i + 1]['price'],
                            'purchase_date': transactions[i]['date'],
                            'sale_date': transactions[i + 1]['date']
                        }
                        holding_periods.append(period)
            
            if not holding_periods:
                return {}
            
            df = pd.DataFrame(holding_periods)
            
            # Calculate holding metrics
            df['holding_years'] = (
                pd.to_datetime(df['sale_date']) - 
                pd.to_datetime(df['purchase_date'])
            ).dt.total_seconds() / (365.25 * 24 * 3600)
            
            df['price_change'] = df['sale_price'] - df['purchase_price']
            df['price_change_pct'] = (
                df['price_change'] / df['purchase_price']
            ) * 100
            
            # Analyze patterns
            patterns = {
                'holding_distribution': {
                    'mean': float(df['holding_years'].mean()),
                    'median': float(df['holding_years'].median()),
                    'std': float(df['holding_years'].std())
                },
                'returns': {
                    'mean_price_change': float(df['price_change'].mean()),
                    'mean_price_change_pct': float(df['price_change_pct'].mean()),
                    'median_price_change_pct': float(df['price_change_pct'].median())
                },
                'by_property_type': self._analyze_holding_by_type(df)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing holding patterns: {str(e)}")
            return {}

    def _analyze_geographic_patterns(self, properties: List[Dict]) -> Dict:
        """Analyze geographic investment patterns"""
        try:
            # Extract location data
            locations = []
            for prop in properties:
                coords = prop.get('coordinates', {})
                if coords.get('latitude') and coords.get('longitude'):
                    locations.append({
                        'property_id': prop.get('property_id'),
                        'property_type': prop.get('property_type'),
                        'total_value': prop.get('assessment', {}).get('total_value'),
                        'latitude': coords['latitude'],
                        'longitude': coords['longitude'],
                        'transactions': len(prop.get('transactions', [])),
                        'permits': len(prop.get('permits', []))
                    })
            
            if not locations:
                return {}
            
            df = pd.DataFrame(locations)
            
            # Perform clustering
            from sklearn.cluster import DBSCAN
            coords = df[['latitude', 'longitude']].values
            
            # Convert cluster radius to degrees (approximate)
            radius_degrees = 0.5 / 69.0  # 0.5 miles to degrees
            
            clustering = DBSCAN(
                eps=radius_degrees,
                min_samples=3,
                metric='euclidean'
            ).fit(coords)
            
            df['cluster'] = clustering.labels_
            
            # Analyze clusters
            patterns = {
                'clusters': self._analyze_clusters(df),
                'hotspots': self._identify_hotspots(df),
                'activity_density': self._calculate_activity_density(df)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing geographic patterns: {str(e)}")
            return {}

    def _calculate_roi(self, property_data: Dict, scenario: Dict) -> Dict:
        """Calculate ROI for investment scenario"""
        try:
            current_value = property_data.get('assessment', {}).get('total_value')
            if not current_value:
                return {}
            
            # Initial investment
            purchase_price = current_value
            improvements = scenario['improvements']
            total_investment = purchase_price + improvements
            
            # Project future value
            future_value = current_value * (
                1 + scenario['appreciation_rate']
            ) ** scenario['holding_period']
            
            # Add improvement value
            if improvements > 0:
                future_value += improvements * 1.5  # Assume 50% return on improvements
            
            # Calculate returns
            total_return = future_value - total_investment
            roi = (total_return / total_investment) * 100
            annual_roi = (
                (1 + roi/100) ** (1/scenario['holding_period']) - 1
            ) * 100
            
            return {
                'scenario': {
                    'holding_period': scenario['holding_period'],
                    'improvements': float(improvements),
                    'appreciation_rate': scenario['appreciation_rate']
                },
                'investment': {
                    'purchase_price': float(purchase_price),
                    'improvements': float(improvements),
                    'total_investment': float(total_investment)
                },
                'returns': {
                    'future_value': float(future_value),
                    'total_return': float(total_return),
                    'roi': float(roi),
                    'annual_roi': float(annual_roi)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating ROI: {str(e)}")
            return {}
