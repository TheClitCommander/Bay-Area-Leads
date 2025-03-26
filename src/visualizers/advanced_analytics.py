"""
Advanced property analytics and visualizations
"""
import logging
from typing import Dict, List, Optional, Tuple
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
import folium
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt

class AdvancedAnalytics:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = Path(__file__).parent.parent.parent / 'output' / 'analytics'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_market_analysis(self, data: List[Dict]) -> str:
        """Create comprehensive market analysis visualization"""
        try:
            df = pd.DataFrame([item.get('properties', {}) for item in data])
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'Price Trends', 'Price Distribution',
                    'Sales Volume', 'Property Types',
                    'Price per Sqft', 'Market Activity'
                ),
                specs=[[{"type": "scatter"}, {"type": "box"}],
                      [{"type": "bar"}, {"type": "pie"}],
                      [{"type": "histogram"}, {"type": "scatter"}]]
            )

            # 1. Price Trends
            df['sale_date'] = pd.to_datetime(df['sale_date'])
            monthly_avg = df.groupby(df['sale_date'].dt.to_period('M')).agg({
                'total_value': 'mean',
                'sale_price': 'mean'
            }).reset_index()
            
            fig.add_trace(
                go.Scatter(
                    x=monthly_avg.index,
                    y=monthly_avg.total_value,
                    name='Assessed Value'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=monthly_avg.index,
                    y=monthly_avg.sale_price,
                    name='Sale Price'
                ),
                row=1, col=1
            )

            # 2. Price Distribution by Property Type
            fig.add_trace(
                go.Box(
                    x=df['property_type'],
                    y=df['total_value'],
                    name='Value Distribution'
                ),
                row=1, col=2
            )

            # 3. Sales Volume
            monthly_sales = df.groupby(df['sale_date'].dt.to_period('M')).size()
            fig.add_trace(
                go.Bar(
                    x=monthly_sales.index.astype(str),
                    y=monthly_sales.values,
                    name='Sales Volume'
                ),
                row=2, col=1
            )

            # 4. Property Type Distribution
            type_counts = df['property_type'].value_counts()
            fig.add_trace(
                go.Pie(
                    labels=type_counts.index,
                    values=type_counts.values,
                    name='Property Types'
                ),
                row=2, col=2
            )

            # 5. Price per Sqft Distribution
            df['price_per_sqft'] = df['total_value'] / df['square_feet']
            fig.add_trace(
                go.Histogram(
                    x=df['price_per_sqft'],
                    name='Price per Sqft'
                ),
                row=3, col=1
            )

            # 6. Market Activity Heatmap
            activity_matrix = self._create_activity_matrix(df)
            fig.add_trace(
                go.Heatmap(
                    z=activity_matrix,
                    name='Market Activity'
                ),
                row=3, col=2
            )

            # Update layout
            fig.update_layout(
                height=1200,
                width=1000,
                title_text="Comprehensive Market Analysis",
                showlegend=True
            )

            # Save visualization
            output_file = self.output_dir / 'market_analysis.html'
            fig.write_html(str(output_file))
            
            return str(output_file)

        except Exception as e:
            self.logger.error(f"Error creating market analysis: {str(e)}")
            return None

    def create_investment_opportunities(self, data: List[Dict]) -> str:
        """Create investment opportunity analysis"""
        try:
            df = pd.DataFrame([item.get('properties', {}) for item in data])
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'ROI Potential', 'Value Growth',
                    'Investment Clusters', 'Risk Analysis'
                )
            )

            # 1. ROI Potential
            roi_scores = self._calculate_roi_potential(df)
            fig.add_trace(
                go.Scatter(
                    x=df['total_value'],
                    y=roi_scores,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=roi_scores,
                        colorscale='Viridis',
                        showscale=True
                    ),
                    name='ROI Potential'
                ),
                row=1, col=1
            )

            # 2. Value Growth Trends
            growth_data = self._calculate_value_growth(df)
            fig.add_trace(
                go.Scatter(
                    x=growth_data.index,
                    y=growth_data.values,
                    name='Value Growth'
                ),
                row=1, col=2
            )

            # 3. Investment Clusters
            clusters = self._create_investment_clusters(df)
            fig.add_trace(
                go.Scatter(
                    x=df['total_value'],
                    y=df['price_per_sqft'],
                    mode='markers',
                    marker=dict(
                        color=clusters,
                        colorscale='Viridis',
                        showscale=True
                    ),
                    name='Investment Clusters'
                ),
                row=2, col=1
            )

            # 4. Risk Analysis
            risk_scores = self._calculate_risk_scores(df)
            fig.add_trace(
                go.Scatter(
                    x=df['total_value'],
                    y=risk_scores,
                    mode='markers',
                    marker=dict(
                        color=risk_scores,
                        colorscale='RdYlGn_r',
                        showscale=True
                    ),
                    name='Risk Analysis'
                ),
                row=2, col=2
            )

            # Update layout
            fig.update_layout(
                height=1000,
                width=1200,
                title_text="Investment Opportunity Analysis"
            )

            # Save visualization
            output_file = self.output_dir / 'investment_opportunities.html'
            fig.write_html(str(output_file))
            
            return str(output_file)

        except Exception as e:
            self.logger.error(f"Error creating investment opportunities: {str(e)}")
            return None

    def create_neighborhood_analysis(self, data: List[Dict]) -> str:
        """Create neighborhood-level analysis"""
        try:
            df = pd.DataFrame([item.get('properties', {}) for item in data])
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Neighborhood Values', 'Property Mix',
                    'Value Trends', 'Development Activity'
                ),
                specs=[[{"type": "choropleth"}, {"type": "pie"}],
                      [{"type": "scatter"}, {"type": "bar"}]]
            )

            # 1. Neighborhood Value Map
            neighborhood_values = self._calculate_neighborhood_values(df)
            fig.add_trace(
                go.Choropleth(
                    locations=neighborhood_values.index,
                    z=neighborhood_values.values,
                    colorscale='Viridis',
                    name='Neighborhood Values'
                ),
                row=1, col=1
            )

            # 2. Property Type Mix by Neighborhood
            type_mix = df.groupby(['neighborhood', 'property_type']).size().unstack()
            fig.add_trace(
                go.Pie(
                    labels=type_mix.columns,
                    values=type_mix.iloc[0],
                    name='Property Mix'
                ),
                row=1, col=2
            )

            # 3. Value Trends by Neighborhood
            trends = self._calculate_neighborhood_trends(df)
            for neighborhood, trend in trends.items():
                fig.add_trace(
                    go.Scatter(
                        x=trend.index,
                        y=trend.values,
                        name=neighborhood
                    ),
                    row=2, col=1
                )

            # 4. Development Activity
            development = self._analyze_development_activity(df)
            fig.add_trace(
                go.Bar(
                    x=development.index,
                    y=development.values,
                    name='Development Activity'
                ),
                row=2, col=2
            )

            # Update layout
            fig.update_layout(
                height=1000,
                width=1200,
                title_text="Neighborhood Analysis"
            )

            # Save visualization
            output_file = self.output_dir / 'neighborhood_analysis.html'
            fig.write_html(str(output_file))
            
            return str(output_file)

        except Exception as e:
            self.logger.error(f"Error creating neighborhood analysis: {str(e)}")
            return None

    def create_predictive_analysis(self, data: List[Dict]) -> str:
        """Create predictive analysis visualization"""
        try:
            df = pd.DataFrame([item.get('properties', {}) for item in data])
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Value Predictions', 'Market Trends',
                    'Growth Potential', 'Risk Factors'
                )
            )

            # 1. Value Predictions
            predictions = self._generate_value_predictions(df)
            fig.add_trace(
                go.Scatter(
                    x=predictions.index,
                    y=predictions['predicted'],
                    name='Predicted Values',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=predictions.index,
                    y=predictions['actual'],
                    name='Actual Values',
                    line=dict(color='red')
                ),
                row=1, col=1
            )

            # 2. Market Trend Analysis
            trends = self._analyze_market_trends(df)
            fig.add_trace(
                go.Scatter(
                    x=trends.index,
                    y=trends['trend'],
                    name='Market Trend',
                    line=dict(color='green')
                ),
                row=1, col=2
            )

            # 3. Growth Potential Analysis
            growth = self._analyze_growth_potential(df)
            fig.add_trace(
                go.Scatter(
                    x=growth.index,
                    y=growth.values,
                    mode='markers',
                    marker=dict(
                        size=10,
                        color=growth.values,
                        colorscale='Viridis',
                        showscale=True
                    ),
                    name='Growth Potential'
                ),
                row=2, col=1
            )

            # 4. Risk Factor Analysis
            risks = self._analyze_risk_factors(df)
            fig.add_trace(
                go.Bar(
                    x=risks.index,
                    y=risks.values,
                    name='Risk Factors'
                ),
                row=2, col=2
            )

            # Update layout
            fig.update_layout(
                height=1000,
                width=1200,
                title_text="Predictive Analysis"
            )

            # Save visualization
            output_file = self.output_dir / 'predictive_analysis.html'
            fig.write_html(str(output_file))
            
            return str(output_file)

        except Exception as e:
            self.logger.error(f"Error creating predictive analysis: {str(e)}")
            return None

    def _calculate_roi_potential(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate ROI potential scores"""
        try:
            # Simplified ROI calculation
            roi = (df['market_value'] - df['total_value']) / df['total_value']
            return roi.values
        except:
            return np.zeros(len(df))

    def _calculate_value_growth(self, df: pd.DataFrame) -> pd.Series:
        """Calculate historical value growth"""
        try:
            return df.groupby('sale_date')['total_value'].mean()
        except:
            return pd.Series()

    def _create_investment_clusters(self, df: pd.DataFrame) -> np.ndarray:
        """Create investment opportunity clusters"""
        try:
            features = df[['total_value', 'price_per_sqft']].values
            kmeans = KMeans(n_clusters=5, random_state=42)
            return kmeans.fit_predict(features)
        except:
            return np.zeros(len(df))

    def _calculate_risk_scores(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate investment risk scores"""
        try:
            # Simplified risk calculation
            risk_factors = [
                df['total_value'].std() / df['total_value'].mean(),
                df['days_on_market'].values if 'days_on_market' in df else 0,
                df['violation_count'].values if 'violation_count' in df else 0
            ]
            return np.mean(risk_factors, axis=0)
        except:
            return np.zeros(len(df))

    def _create_activity_matrix(self, df: pd.DataFrame) -> np.ndarray:
        """Create market activity heatmap matrix"""
        try:
            # Create 12x12 matrix for monthly activity
            matrix = np.zeros((12, 12))
            for i in range(12):
                for j in range(12):
                    month_data = df[df['sale_date'].dt.month == (i + 1)]
                    matrix[i, j] = len(month_data)
            return matrix
        except:
            return np.zeros((12, 12))
