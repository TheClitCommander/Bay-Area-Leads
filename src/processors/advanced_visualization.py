"""
Advanced visualization capabilities for property data
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
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import json

class AdvancedVisualization:
    """
    Advanced visualization including:
    1. Interactive property maps
    2. Market trend visualizations
    3. Network visualizations
    4. Investment analysis charts
    5. Comparative analysis plots
    6. PDF report generation
    7. Custom dashboards
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Configure visualization parameters
        self.params = {
            'map_zoom': 12,
            'chart_height': 600,
            'chart_width': 800,
            'color_scheme': 'viridis',
            'animation_frame': 500
        }
        
        if 'viz_params' in config:
            self.params.update(config['viz_params'])
        
        # Set style
        plt.style.use('seaborn')
        
        # Configure color schemes
        self.color_schemes = {
            'primary': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'],
            'sequential': px.colors.sequential.Viridis,
            'diverging': px.colors.diverging.RdYlBu,
            'qualitative': px.colors.qualitative.Set3
        }

    def create_property_map(self,
                          properties: List[Dict],
                          analysis_results: Dict = None) -> Dict:
        """
        Create interactive property map
        """
        try:
            # Create base map
            center = self._calculate_map_center(properties)
            m = folium.Map(
                location=center,
                zoom_start=self.params['map_zoom']
            )
            
            # Add property markers
            marker_cluster = plugins.MarkerCluster().add_to(m)
            
            for prop in properties:
                # Get coordinates
                coords = prop.get('coordinates', {})
                if not coords.get('latitude') or not coords.get('longitude'):
                    continue
                
                # Create popup content
                popup_content = self._create_property_popup(
                    prop,
                    analysis_results
                )
                
                # Add marker
                folium.Marker(
                    location=[coords['latitude'], coords['longitude']],
                    popup=popup_content,
                    icon=self._get_property_icon(prop)
                ).add_to(marker_cluster)
            
            # Add heatmap layer
            heat_data = [
                [
                    prop['coordinates']['latitude'],
                    prop['coordinates']['longitude'],
                    self._calculate_heat_weight(prop)
                ]
                for prop in properties
                if prop.get('coordinates', {}).get('latitude')
                and prop.get('coordinates', {}).get('longitude')
            ]
            
            plugins.HeatMap(heat_data).add_to(m)
            
            # Add choropleth layer if available
            if analysis_results and 'geographic' in analysis_results:
                self._add_choropleth_layer(m, analysis_results['geographic'])
            
            return {
                'map': m,
                'center': center,
                'zoom': self.params['map_zoom']
            }
            
        except Exception as e:
            self.logger.error(f"Error creating property map: {str(e)}")
            return {}

    def create_market_visualizations(self,
                                   market_data: Dict,
                                   analysis_results: Dict = None) -> Dict:
        """
        Create market trend visualizations
        """
        try:
            visualizations = {}
            
            # Create price trends
            visualizations['price_trends'] = self._create_price_trends_chart(
                market_data
            )
            
            # Create volume trends
            visualizations['volume_trends'] = self._create_volume_trends_chart(
                market_data
            )
            
            # Create market segments
            visualizations['segments'] = self._create_segment_analysis_chart(
                market_data
            )
            
            # Create comparative analysis
            if analysis_results:
                visualizations['comparison'] = self._create_market_comparison_chart(
                    market_data,
                    analysis_results
                )
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating market visualizations: {str(e)}")
            return {}

    def create_network_visualizations(self,
                                    network_data: Dict,
                                    analysis_results: Dict = None) -> Dict:
        """
        Create network visualizations
        """
        try:
            visualizations = {}
            
            # Create owner network
            visualizations['owner_network'] = self._create_owner_network_chart(
                network_data
            )
            
            # Create transaction network
            visualizations['transaction_network'] = self._create_transaction_network_chart(
                network_data
            )
            
            # Create relationship network
            visualizations['relationship_network'] = self._create_relationship_network_chart(
                network_data
            )
            
            # Create community analysis
            if analysis_results:
                visualizations['communities'] = self._create_community_analysis_chart(
                    network_data,
                    analysis_results
                )
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating network visualizations: {str(e)}")
            return {}

    def create_investment_visualizations(self,
                                       investment_data: Dict,
                                       analysis_results: Dict = None) -> Dict:
        """
        Create investment analysis visualizations
        """
        try:
            visualizations = {}
            
            # Create ROI analysis
            visualizations['roi_analysis'] = self._create_roi_analysis_chart(
                investment_data
            )
            
            # Create opportunity analysis
            visualizations['opportunities'] = self._create_opportunity_analysis_chart(
                investment_data
            )
            
            # Create risk analysis
            visualizations['risks'] = self._create_risk_analysis_chart(
                investment_data
            )
            
            # Create comparative analysis
            if analysis_results:
                visualizations['comparison'] = self._create_investment_comparison_chart(
                    investment_data,
                    analysis_results
                )
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating investment visualizations: {str(e)}")
            return {}

    def create_comparative_visualizations(self,
                                        data1: Dict,
                                        data2: Dict) -> Dict:
        """
        Create comparative visualizations
        """
        try:
            visualizations = {}
            
            # Create feature comparison
            visualizations['features'] = self._create_feature_comparison_chart(
                data1,
                data2
            )
            
            # Create price comparison
            visualizations['prices'] = self._create_price_comparison_chart(
                data1,
                data2
            )
            
            # Create trend comparison
            visualizations['trends'] = self._create_trend_comparison_chart(
                data1,
                data2
            )
            
            # Create metric comparison
            visualizations['metrics'] = self._create_metric_comparison_chart(
                data1,
                data2
            )
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating comparative visualizations: {str(e)}")
            return {}

    def generate_pdf_report(self,
                           data: Dict,
                           report_type: str = 'full') -> bytes:
        """
        Generate PDF report with visualizations
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                'report.pdf',
                pagesize=letter
            )
            
            # Generate content based on report type
            if report_type == 'full':
                content = self._generate_full_report_content(data)
            elif report_type == 'summary':
                content = self._generate_summary_report_content(data)
            elif report_type == 'investment':
                content = self._generate_investment_report_content(data)
            else:
                content = self._generate_custom_report_content(
                    data,
                    report_type
                )
            
            # Build document
            doc.build(content)
            
            # Read PDF content
            with open('report.pdf', 'rb') as f:
                pdf_content = f.read()
            
            return pdf_content
            
        except Exception as e:
            self.logger.error(f"Error generating PDF report: {str(e)}")
            return b''

    def create_custom_dashboard(self,
                              data: Dict,
                              layout: Dict) -> Dict:
        """
        Create custom interactive dashboard
        """
        try:
            dashboard = {}
            
            # Create figure with subplots
            fig = make_subplots(
                rows=layout['rows'],
                cols=layout['cols'],
                subplot_titles=layout.get('titles', []),
                specs=layout.get('specs', []),
                vertical_spacing=0.1,
                horizontal_spacing=0.1
            )
            
            # Add plots based on layout
            for plot in layout['plots']:
                self._add_dashboard_plot(
                    fig,
                    data,
                    plot
                )
            
            # Update layout
            fig.update_layout(
                height=self.params['chart_height'],
                width=self.params['chart_width'],
                showlegend=True,
                title_text=layout.get('title', ''),
                template='plotly_white'
            )
            
            dashboard['figure'] = fig
            dashboard['layout'] = layout
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error creating custom dashboard: {str(e)}")
            return {}
