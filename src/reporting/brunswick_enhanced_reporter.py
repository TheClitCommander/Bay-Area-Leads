"""
Enhanced reporting capabilities for Brunswick data
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Optional, Union, Tuple
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
from ..storage.brunswick_data_manager import BrunswickDataManager

class BrunswickEnhancedReporter:
    def __init__(self, data_manager: BrunswickDataManager):
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        self.report_dir = Path("reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up plotting styles
        plt.style.use('seaborn-v0_8')
        sns.set_theme(style="whitegrid")
        
    def generate_market_analysis(self, period: str = "last_month") -> Dict:
        """Generate comprehensive market analysis"""
        # Get data
        businesses = self.data_manager.search(
            query=self._get_time_filter(period),
            item_type="businesses"
        )
        properties = self.data_manager.search(
            query=self._get_time_filter(period),
            item_type="properties"
        )
        
        # Convert to DataFrames
        bdf = pd.DataFrame(businesses)
        pdf = pd.DataFrame(properties)
        
        analysis = {
            # Business Activity
            'business_metrics': self._analyze_business_activity(bdf),
            
            # Property Analysis
            'property_metrics': self._analyze_property_market(pdf),
            
            # Development Activity
            'development_metrics': self._analyze_development_activity(bdf, pdf),
            
            # Geographic Analysis
            'geographic_metrics': self._analyze_geographic_patterns(bdf, pdf)
        }
        
        # Generate visualizations
        analysis['visualizations'] = self._create_market_visualizations(bdf, pdf)
        
        return analysis
        
    def generate_trend_report(self, periods: int = 12) -> Dict:
        """Generate trend analysis over multiple periods"""
        # Get historical data
        historical_data = self._get_historical_data(periods)
        
        report = {
            # Business Trends
            'business_trends': self._analyze_business_activity(historical_data['businesses']),
            
            # Property Trends
            'property_trends': self._analyze_property_market(historical_data['properties']),
            
            # Market Indicators
            'market_indicators': {
                'business_growth': len(historical_data.get('businesses', [])),
                'property_value': sum(p.get('assessment', 0) for p in historical_data.get('properties', [])),
                'active_licenses': sum(1 for b in historical_data.get('businesses', []) if b.get('license_status') == 'ACTIVE')
            }
        }
        
        # Generate visualizations
        report['visualizations'] = self._create_trend_visualizations(historical_data)
        
        return report
        
    def _analyze_business_activity(self, data: List[Dict]) -> Dict:
        """Analyze business activity metrics"""
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        # Debug log available columns
        self.logger.info(f"Available columns in business data: {df.columns.tolist()}")
        
        # Convert dates if column exists
        if 'founding_date' in df.columns:
            df['founding_date'] = pd.to_datetime(df['founding_date'])
        else:
            # Use a default date if founding_date is missing
            df['founding_date'] = pd.to_datetime('2020-01-01')
        
        metrics = {
            'total_businesses': len(df)
        }
        
        # Add new businesses count if founding_date exists
        if 'founding_date' in df.columns:
            metrics['new_businesses_30d'] = len(df[df['founding_date'] >= thirty_days_ago])
            metrics['avg_age'] = (now - df['founding_date']).mean().days / 365.25
        else:
            metrics['new_businesses_30d'] = 0
            metrics['avg_age'] = 0
        
        # Add business types if type exists
        if 'type' in df.columns:
            metrics['business_types'] = df['type'].value_counts().to_dict()
        else:
            metrics['business_types'] = {}
        
        # Add license statistics if license_status exists
        if 'license_status' in df.columns:
            metrics['license_statistics'] = {
                'active': len(df[df['license_status'] == 'ACTIVE']),
                'pending': len(df[df['license_status'] == 'PENDING']),
                'expired': len(df[df['license_status'] == 'EXPIRED'])
            }
        else:
            metrics['license_statistics'] = {
                'active': 0,
                'pending': 0,
                'expired': 0
            }
        
        return metrics
        
    def _analyze_property_market(self, data: List[Dict]) -> Dict:
        """Analyze property market metrics"""
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        
        metrics = {
            'total_properties': len(df)
        }
        
        # Add assessment metrics if assessment exists
        if 'assessment' in df.columns:
            metrics.update({
                'avg_assessment': df['assessment'].mean(),
                'median_assessment': df['assessment'].median(),
                'assessment_range': {
                    'min': df['assessment'].min(),
                    'max': df['assessment'].max()
                }
            })
        else:
            metrics.update({
                'avg_assessment': 0,
                'median_assessment': 0,
                'assessment_range': {
                    'min': 0,
                    'max': 0
                }
            })
        
        # Add zoning distribution if zoning exists
        if 'zoning' in df.columns:
            metrics['zoning_distribution'] = df['zoning'].value_counts().to_dict()
        else:
            metrics['zoning_distribution'] = {}
        
        # Add property types if type exists
        if 'type' in df.columns:
            metrics['property_types'] = df['type'].value_counts().to_dict()
        else:
            metrics['property_types'] = {}
        
        return metrics
        
    def _analyze_development_activity(
        self,
        business_data: List[Dict],
        property_data: List[Dict]
    ) -> Dict:
        # Convert data to DataFrames
        bdf = pd.DataFrame(business_data)
        pdf = pd.DataFrame(property_data)
        """Analyze development and permit activity"""
        metrics = {
            'active_permits': {
                'total': len(pdf[pdf['permit_status'] == 'ACTIVE']),
                'by_type': pdf['permit_type'].value_counts().to_dict()
            },
            'construction_value': pdf['permit_value'].sum(),
            'development_areas': pdf['zoning'].value_counts().to_dict(),
            'recent_changes': {
                'new_construction': len(pdf[pdf['permit_type'] == 'NEW_CONSTRUCTION']),
                'renovations': len(pdf[pdf['permit_type'] == 'RENOVATION']),
                'changes_of_use': len(pdf[pdf['permit_type'] == 'CHANGE_OF_USE'])
            }
        }
        
        return metrics
        
    def _analyze_geographic_patterns(
        self,
        business_data: List[Dict],
        property_data: List[Dict]
    ) -> Dict:
        # Convert data to DataFrames
        bdf = pd.DataFrame(business_data)
        pdf = pd.DataFrame(property_data)
        """Analyze geographic distribution and patterns"""
        metrics = {
            'business_density': self._calculate_density(bdf),
            'property_values': self._calculate_value_distribution(pdf),
            'development_hotspots': self._identify_hotspots(pdf),
            'market_clusters': self._identify_clusters(bdf, pdf)
        }
        
        return metrics
        
    def _create_market_visualizations(
        self,
        bdf: pd.DataFrame,
        pdf: pd.DataFrame
    ) -> Dict[str, str]:
        """Create visualizations for market analysis"""
        visualizations = {}
        
        # Business type distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        bdf['type'].value_counts().plot(kind='bar', ax=ax)
        ax.set_title('Business Type Distribution')
        ax.set_xlabel('Business Type')
        ax.set_ylabel('Count')
        plt.xticks(rotation=45)
        visualizations['business_types'] = self._save_figure(fig, 'business_types')
        
        # Property value distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(data=pdf, x='assessment', bins=30, ax=ax)
        ax.set_title('Property Value Distribution')
        ax.set_xlabel('Assessment Value ($)')
        visualizations['property_values'] = self._save_figure(fig, 'property_values')
        
        # Development activity
        fig, ax = plt.subplots(figsize=(10, 6))
        pdf['permit_type'].value_counts().plot(kind='bar', ax=ax)
        ax.set_title('Development Activity by Permit Type')
        ax.set_xlabel('Permit Type')
        ax.set_ylabel('Count')
        plt.xticks(rotation=45)
        visualizations['development_activity'] = self._save_figure(fig, 'development_activity')
        
        return visualizations
        
    def _create_trend_visualizations(self, data: Dict) -> Dict[str, str]:
        """Create visualizations for trend analysis"""
        visualizations = {}
        
        # Business growth trend
        fig, ax = plt.subplots(figsize=(12, 6))
        df_businesses = pd.DataFrame(data['businesses'])
        if len(df_businesses) > 0:
            # Create period from founding_date if available
            if 'founding_date' in df_businesses.columns:
                df_businesses['period'] = pd.to_datetime(df_businesses['founding_date']).dt.to_period('M')
                business_counts = df_businesses.groupby('period').size()
                business_counts.plot(ax=ax)
                ax.set_title('Business Growth Trend')
                ax.set_xlabel('Period')
                ax.set_ylabel('Total Businesses')
        visualizations['business_growth'] = self._save_figure(fig, 'business_growth')
        plt.close(fig)
        
        # Property value trend
        fig, ax = plt.subplots(figsize=(12, 6))
        df_properties = pd.DataFrame(data['properties'])
        if len(df_properties) > 0:
            # Create period from last_updated if available
            if 'last_updated' in df_properties.columns and 'assessment' in df_properties.columns:
                df_properties['period'] = pd.to_datetime(df_properties['last_updated']).dt.to_period('M')
                avg_values = df_properties.groupby('period')['assessment'].mean()
                avg_values.plot(ax=ax)
                ax.set_title('Property Value Trend')
                ax.set_xlabel('Period')
                ax.set_ylabel('Average Value ($)')
        visualizations['property_values'] = self._save_figure(fig, 'property_values')
        plt.close(fig)
        
        return visualizations
        
    def _save_figure(self, fig: plt.Figure, name: str) -> str:
        """Save figure and return path"""
        path = self.report_dir / f"{name}.png"
        fig.savefig(path, bbox_inches='tight', dpi=300)
        plt.close(fig)
        return str(path)
        
    def _get_historical_data(self, periods: int) -> Dict:
        """Get historical data for trend analysis"""
        data = {
            'businesses': [],
            'properties': []
        }
        
        for i in range(periods):
            period_start = datetime.now() - timedelta(days=30 * (i + 1))
            period_end = datetime.now() - timedelta(days=30 * i)
            
            # Get business data
            businesses = self.data_manager.search(
                query={
                    'last_updated': {
                        'gte': period_start.isoformat(),
                        'lt': period_end.isoformat()
                    }
                },
                item_type="businesses"
            )
            
            # Get property data
            properties = self.data_manager.search(
                query={
                    'last_updated': {
                        'gte': period_start.isoformat(),
                        'lt': period_end.isoformat()
                    }
                },
                item_type="properties"
            )
            
            # Add period information
            period_data = {
                'period': i,
                'start_date': period_start,
                'end_date': period_end,
                'businesses': businesses,
                'properties': properties
            }
            
            data['businesses'].append(period_data)
            
        return data
        
    def _calculate_density(self, df: pd.DataFrame) -> Dict:
        """Calculate business density by area"""
        return df.groupby('neighborhood')['id'].count().to_dict()
        
    def _calculate_value_distribution(self, df: pd.DataFrame) -> Dict:
        """Calculate property value distribution by area"""
        return df.groupby('neighborhood')['assessment'].mean().to_dict()
        
    def _identify_hotspots(self, data: List[Dict]) -> List[Dict]:
        """Identify development hotspots"""
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        hotspots = []
        
        # Group by neighborhood and count permits
        permit_counts = df.groupby('neighborhood')['id'].count()
        
        # Find areas with high permit activity
        for area, count in permit_counts.items():
            if count > permit_counts.mean() + permit_counts.std():
                hotspots.append({
                    'area': area,
                    'permit_count': count,
                    'avg_value': df[df['neighborhood'] == area]['permit_value'].mean()
                })
                
        return hotspots
        
    def _identify_clusters(self, business_data: List[Dict], property_data: List[Dict]) -> List[Dict]:
        """Identify business and property clusters"""
        # Convert data to DataFrames
        bdf = pd.DataFrame(business_data)
        pdf = pd.DataFrame(property_data)
        clusters = []
        
        # Group by neighborhood
        for neighborhood in bdf['neighborhood'].unique():
            business_count = len(bdf[bdf['neighborhood'] == neighborhood])
            avg_property_value = pdf[
                pdf['neighborhood'] == neighborhood
            ]['assessment'].mean()
            
            if business_count > bdf.groupby('neighborhood').size().mean():
                clusters.append({
                    'neighborhood': neighborhood,
                    'business_count': business_count,
                    'avg_property_value': avg_property_value,
                    'dominant_type': bdf[
                        bdf['neighborhood'] == neighborhood
                    ]['type'].mode()[0]
                })
                
        return clusters
        
    def _get_time_filter(self, period: str) -> Dict:
        """Convert time period to query filter"""
        now = datetime.now()
        
        if period == "last_month":
            start_date = now - timedelta(days=30)
        elif period == "last_quarter":
            start_date = now - timedelta(days=90)
        elif period == "last_year":
            start_date = now - timedelta(days=365)
        else:
            raise ValueError(f"Unsupported time period: {period}")
            
        return {
            "last_updated": {
                "gte": start_date.isoformat()
            }
        }
