"""
Generates advanced visualizations and reports for property analysis
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import folium
from folium import plugins
import seaborn as sns
import matplotlib.pyplot as plt
import jinja2
import pdfkit

class VisualizationGenerator:
    """
    Generates visualizations and reports including:
    1. Interactive property maps
    2. Market trend visualizations
    3. Investment analysis charts
    4. Comparative analysis plots
    5. PDF reports
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Configure visualization settings
        self.settings = {
            'color_scheme': config.get('color_scheme', 'viridis'),
            'map_style': config.get('map_style', 'OpenStreetMap'),
            'plot_height': config.get('plot_height', 600),
            'plot_width': config.get('plot_width', 800),
            'report_template': config.get('report_template', 'default')
        }
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('templates')
        )

    def create_property_map(self, properties: List[Dict]) -> Dict:
        """
        Create interactive map visualization
        """
        try:
            # Create base map
            center_lat = np.mean([
                p['coordinates']['latitude']
                for p in properties
                if p.get('coordinates')
            ])
            center_lon = np.mean([
                p['coordinates']['longitude']
                for p in properties
                if p.get('coordinates')
            ])
            
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=13,
                tiles=self.settings['map_style']
            )
            
            # Add property markers
            for prop in properties:
                try:
                    coords = prop.get('coordinates', {})
                    if coords.get('latitude') and coords.get('longitude'):
                        # Create popup content
                        popup_content = self._create_map_popup(prop)
                        
                        # Add marker
                        folium.CircleMarker(
                            location=[coords['latitude'], coords['longitude']],
                            radius=8,
                            popup=popup_content,
                            color=self._get_marker_color(prop),
                            fill=True
                        ).add_to(m)
                        
                except Exception as e:
                    self.logger.warning(f"Error adding marker: {str(e)}")
                    continue
            
            # Add heatmap layer
            heat_data = [
                [
                    p['coordinates']['latitude'],
                    p['coordinates']['longitude'],
                    self._calculate_heat_weight(p)
                ]
                for p in properties
                if p.get('coordinates')
            ]
            
            plugins.HeatMap(heat_data).add_to(m)
            
            # Add clustering
            marker_cluster = plugins.MarkerCluster().add_to(m)
            
            for prop in properties:
                coords = prop.get('coordinates', {})
                if coords.get('latitude') and coords.get('longitude'):
                    folium.Marker(
                        [coords['latitude'], coords['longitude']],
                        popup=self._create_map_popup(prop)
                    ).add_to(marker_cluster)
            
            # Save map
            map_file = 'property_map.html'
            m.save(map_file)
            
            return {
                'map_file': map_file,
                'center': {
                    'latitude': center_lat,
                    'longitude': center_lon
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error creating property map: {str(e)}")
            return {}

    def create_market_visualizations(self, market_data: Dict) -> Dict:
        """
        Create market trend visualizations
        """
        try:
            visualizations = {}
            
            # Create price trends plot
            price_fig = self._create_price_trends_plot(market_data)
            visualizations['price_trends'] = price_fig
            
            # Create volume analysis plot
            volume_fig = self._create_volume_analysis_plot(market_data)
            visualizations['volume_analysis'] = volume_fig
            
            # Create market indicators plot
            indicators_fig = self._create_market_indicators_plot(market_data)
            visualizations['market_indicators'] = indicators_fig
            
            # Create seasonal patterns plot
            seasonal_fig = self._create_seasonal_patterns_plot(market_data)
            visualizations['seasonal_patterns'] = seasonal_fig
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating market visualizations: {str(e)}")
            return {}

    def create_investment_visualizations(self, 
                                      investment_data: Dict,
                                      property_data: Dict) -> Dict:
        """
        Create investment analysis visualizations
        """
        try:
            visualizations = {}
            
            # Create ROI analysis plot
            roi_fig = self._create_roi_analysis_plot(
                investment_data,
                property_data
            )
            visualizations['roi_analysis'] = roi_fig
            
            # Create cash flow projection plot
            cashflow_fig = self._create_cashflow_projection_plot(
                investment_data
            )
            visualizations['cashflow_projection'] = cashflow_fig
            
            # Create risk analysis plot
            risk_fig = self._create_risk_analysis_plot(investment_data)
            visualizations['risk_analysis'] = risk_fig
            
            # Create scenario comparison plot
            scenario_fig = self._create_scenario_comparison_plot(
                investment_data
            )
            visualizations['scenario_comparison'] = scenario_fig
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating investment visualizations: {str(e)}")
            return {}

    def create_comparative_visualizations(self,
                                       target_property: Dict,
                                       comparable_properties: List[Dict]) -> Dict:
        """
        Create comparative analysis visualizations
        """
        try:
            visualizations = {}
            
            # Create value comparison plot
            value_fig = self._create_value_comparison_plot(
                target_property,
                comparable_properties
            )
            visualizations['value_comparison'] = value_fig
            
            # Create feature comparison plot
            feature_fig = self._create_feature_comparison_plot(
                target_property,
                comparable_properties
            )
            visualizations['feature_comparison'] = feature_fig
            
            # Create market position plot
            position_fig = self._create_market_position_plot(
                target_property,
                comparable_properties
            )
            visualizations['market_position'] = position_fig
            
            # Create opportunity score comparison
            score_fig = self._create_score_comparison_plot(
                target_property,
                comparable_properties
            )
            visualizations['score_comparison'] = score_fig
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating comparative visualizations: {str(e)}")
            return {}

    def generate_property_report(self,
                               property_data: Dict,
                               analysis_results: Dict) -> str:
        """
        Generate comprehensive PDF report
        """
        try:
            # Load report template
            template = self.jinja_env.get_template(
                f"{self.settings['report_template']}.html"
            )
            
            # Prepare report data
            report_data = {
                'property': property_data,
                'analysis': analysis_results,
                'visualizations': self._create_report_visualizations(
                    property_data,
                    analysis_results
                ),
                'insights': self._generate_report_insights(
                    property_data,
                    analysis_results
                ),
                'recommendations': self._generate_recommendations(
                    property_data,
                    analysis_results
                ),
                'generated_at': datetime.now().isoformat()
            }
            
            # Render template
            html_content = template.render(**report_data)
            
            # Convert to PDF
            pdf_file = f"property_report_{property_data['property_id']}.pdf"
            
            pdfkit.from_string(
                html_content,
                pdf_file,
                options={
                    'page-size': 'Letter',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in'
                }
            )
            
            return pdf_file
            
        except Exception as e:
            self.logger.error(f"Error generating property report: {str(e)}")
            return ""

    def _create_map_popup(self, property_data: Dict) -> str:
        """Create HTML content for map popup"""
        try:
            content = f"""
            <div style='width:200px'>
                <h4>{property_data.get('address', 'N/A')}</h4>
                <p>
                    <strong>Value:</strong> ${property_data.get('assessment', {}).get('total_value', 0):,.2f}<br>
                    <strong>Type:</strong> {property_data.get('property_type', 'N/A')}<br>
                    <strong>Size:</strong> {property_data.get('square_feet', 0):,} sq ft
                </p>
                <p>
                    <strong>Score:</strong> {property_data.get('opportunity_score', 0):.2f}<br>
                    <strong>Type:</strong> {property_data.get('opportunity_type', 'N/A')}
                </p>
            </div>
            """
            return content
            
        except Exception as e:
            self.logger.error(f"Error creating map popup: {str(e)}")
            return ""

    def _get_marker_color(self, property_data: Dict) -> str:
        """Determine marker color based on property attributes"""
        try:
            # Color based on opportunity score
            score = property_data.get('opportunity_score', 0)
            
            if score >= 0.8:
                return 'darkgreen'
            elif score >= 0.6:
                return 'green'
            elif score >= 0.4:
                return 'orange'
            elif score >= 0.2:
                return 'red'
            else:
                return 'darkred'
            
        except Exception as e:
            self.logger.error(f"Error getting marker color: {str(e)}")
            return 'gray'

    def _calculate_heat_weight(self, property_data: Dict) -> float:
        """Calculate weight for heatmap"""
        try:
            # Combine multiple factors for weight
            weights = {
                'opportunity_score': property_data.get('opportunity_score', 0),
                'value_score': property_data.get('value_score', 0),
                'growth_score': property_data.get('growth_score', 0)
            }
            
            # Calculate weighted average
            weight = sum(weights.values()) / len(weights)
            
            return float(weight)
            
        except Exception as e:
            self.logger.error(f"Error calculating heat weight: {str(e)}")
            return 0.0

    def _create_price_trends_plot(self, market_data: Dict) -> go.Figure:
        """Create price trends visualization"""
        try:
            # Create figure with secondary y-axis
            fig = make_subplots(
                specs=[[{"secondary_y": True}]]
            )
            
            # Add price trend line
            fig.add_trace(
                go.Scatter(
                    x=market_data['dates'],
                    y=market_data['median_prices'],
                    name="Median Price",
                    line=dict(color='blue')
                ),
                secondary_y=False
            )
            
            # Add price change percentage
            fig.add_trace(
                go.Scatter(
                    x=market_data['dates'],
                    y=market_data['price_change_pct'],
                    name="Price Change %",
                    line=dict(color='red')
                ),
                secondary_y=True
            )
            
            # Update layout
            fig.update_layout(
                title="Price Trends Analysis",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                yaxis2_title="Price Change (%)",
                height=self.settings['plot_height'],
                width=self.settings['plot_width']
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating price trends plot: {str(e)}")
            return None

    def _create_volume_analysis_plot(self, market_data: Dict) -> go.Figure:
        """Create volume analysis visualization"""
        try:
            fig = go.Figure()
            
            # Add volume bars
            fig.add_trace(
                go.Bar(
                    x=market_data['dates'],
                    y=market_data['sales_volume'],
                    name="Sales Volume",
                    marker_color='blue'
                )
            )
            
            # Add moving average line
            fig.add_trace(
                go.Scatter(
                    x=market_data['dates'],
                    y=market_data['volume_ma'],
                    name="Volume MA (3m)",
                    line=dict(color='red')
                )
            )
            
            # Update layout
            fig.update_layout(
                title="Sales Volume Analysis",
                xaxis_title="Date",
                yaxis_title="Number of Sales",
                height=self.settings['plot_height'],
                width=self.settings['plot_width']
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating volume analysis plot: {str(e)}")
            return None

    def _create_market_indicators_plot(self, market_data: Dict) -> go.Figure:
        """Create market indicators visualization"""
        try:
            # Create figure with multiple subplots
            fig = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=(
                    "Days on Market",
                    "Inventory Levels",
                    "Price Reductions",
                    "Absorption Rate"
                )
            )
            
            # Add days on market
            fig.add_trace(
                go.Scatter(
                    x=market_data['dates'],
                    y=market_data['days_on_market'],
                    name="DOM"
                ),
                row=1, col=1
            )
            
            # Add inventory levels
            fig.add_trace(
                go.Bar(
                    x=market_data['dates'],
                    y=market_data['inventory'],
                    name="Inventory"
                ),
                row=1, col=2
            )
            
            # Add price reductions
            fig.add_trace(
                go.Scatter(
                    x=market_data['dates'],
                    y=market_data['price_reductions'],
                    name="Price Cuts"
                ),
                row=2, col=1
            )
            
            # Add absorption rate
            fig.add_trace(
                go.Scatter(
                    x=market_data['dates'],
                    y=market_data['absorption_rate'],
                    name="Absorption"
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                height=self.settings['plot_height'],
                width=self.settings['plot_width'],
                title_text="Market Health Indicators"
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating market indicators plot: {str(e)}")
            return None
