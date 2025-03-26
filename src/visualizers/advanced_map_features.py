"""
Advanced map visualization features
"""
import logging
from typing import Dict, List, Optional
import folium
from folium import plugins
import pandas as pd
import numpy as np
from datetime import datetime
import json
import branca.colormap as cm
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

class AdvancedMapFeatures:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = Path(__file__).parent.parent.parent / 'output' / 'visualizations'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def add_heatmap(self, m: folium.Map, data: List[Dict], value_field: str) -> folium.Map:
        """Add heatmap layer based on property values"""
        try:
            points = []
            for item in data:
                if 'geometry' in item:
                    coords = item['geometry'].get('coordinates', [[]])[0][0]
                    value = item.get('properties', {}).get(value_field, 0)
                    points.append([coords[1], coords[0], value])

            plugins.HeatMap(points).add_to(m)
            return m

        except Exception as e:
            self.logger.error(f"Error adding heatmap: {str(e)}")
            return m

    def add_cluster_markers(self, m: folium.Map, data: List[Dict]) -> folium.Map:
        """Add clustered markers for properties"""
        try:
            marker_cluster = plugins.MarkerCluster(name="Property Clusters")

            for item in data:
                if 'geometry' in item:
                    coords = item['geometry'].get('coordinates', [[]])[0][0]
                    props = item.get('properties', {})
                    
                    popup_html = self._create_detailed_popup(props)
                    
                    folium.Marker(
                        [coords[1], coords[0]],
                        popup=folium.Popup(popup_html, max_width=300),
                        icon=self._get_property_icon(props)
                    ).add_to(marker_cluster)

            marker_cluster.add_to(m)
            return m

        except Exception as e:
            self.logger.error(f"Error adding clusters: {str(e)}")
            return m

    def add_time_slider(self, m: folium.Map, data: List[Dict], 
                       date_field: str) -> folium.Map:
        """Add time slider for temporal analysis"""
        try:
            # Group data by date
            time_data = {}
            for item in data:
                date_str = item.get('properties', {}).get(date_field)
                if date_str:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    if date not in time_data:
                        time_data[date] = []
                    time_data[date].append(item)

            # Create time slider
            time_index = plugins.TimeSliderChoropleth(
                {str(date): self._create_time_entry(items) 
                 for date, items in time_data.items()}
            ).add_to(m)

            return m

        except Exception as e:
            self.logger.error(f"Error adding time slider: {str(e)}")
            return m

    def create_3d_visualization(self, data: List[Dict], 
                              height_field: str = 'total_value') -> str:
        """Create 3D visualization of properties"""
        try:
            # Extract coordinates and heights
            xs, ys, zs = [], [], []
            labels = []

            for item in data:
                if 'geometry' in item:
                    coords = item['geometry'].get('coordinates', [[]])[0]
                    height = item.get('properties', {}).get(height_field, 0)
                    
                    for coord in coords:
                        xs.append(coord[0])
                        ys.append(coord[1])
                        zs.append(height)
                        labels.append(
                            f"Address: {item.get('properties', {}).get('address', 'N/A')}<br>"
                            f"Value: ${height:,.2f}"
                        )

            # Create 3D scatter plot
            fig = go.Figure(data=[go.Scatter3d(
                x=xs, y=ys, z=zs,
                mode='markers',
                marker=dict(
                    size=8,
                    color=zs,
                    colorscale='Viridis',
                    opacity=0.8
                ),
                text=labels,
                hoverinfo='text'
            )])

            # Update layout
            fig.update_layout(
                title='3D Property Visualization',
                scene=dict(
                    xaxis_title='Longitude',
                    yaxis_title='Latitude',
                    zaxis_title=height_field.replace('_', ' ').title()
                )
            )

            # Save to file
            output_file = self.output_dir / '3d_visualization.html'
            fig.write_html(str(output_file))

            return str(output_file)

        except Exception as e:
            self.logger.error(f"Error creating 3D visualization: {str(e)}")
            return None

    def create_analytics_dashboard(self, data: List[Dict]) -> str:
        """Create analytics dashboard with property insights"""
        try:
            # Convert data to pandas DataFrame
            df = pd.DataFrame([item.get('properties', {}) for item in data])

            # Create dashboard with multiple plots
            fig = go.Figure()

            # Value distribution
            fig.add_trace(go.Histogram(
                x=df['total_value'],
                name='Value Distribution',
                nbinsx=30
            ))

            # Property types
            type_counts = df['property_type'].value_counts()
            fig.add_trace(go.Pie(
                labels=type_counts.index,
                values=type_counts.values,
                name='Property Types'
            ))

            # Time series if available
            if 'sale_date' in df.columns:
                df['sale_date'] = pd.to_datetime(df['sale_date'])
                monthly_sales = df.groupby(df['sale_date'].dt.to_period('M')).size()
                fig.add_trace(go.Scatter(
                    x=monthly_sales.index.astype(str),
                    y=monthly_sales.values,
                    name='Monthly Sales'
                ))

            # Update layout
            fig.update_layout(
                title='Property Analytics Dashboard',
                height=800,
                grid={'rows': 2, 'columns': 2}
            )

            # Save dashboard
            output_file = self.output_dir / 'analytics_dashboard.html'
            fig.write_html(str(output_file))

            return str(output_file)

        except Exception as e:
            self.logger.error(f"Error creating dashboard: {str(e)}")
            return None

    def _create_detailed_popup(self, props: Dict) -> str:
        """Create detailed popup with property information"""
        try:
            return f"""
                <div style="width:300px">
                    <h3>{props.get('address', 'N/A')}</h3>
                    <hr>
                    <h4>Property Details</h4>
                    <table style="width:100%">
                        <tr><td>Owner:</td><td>{props.get('owner_name', 'N/A')}</td></tr>
                        <tr><td>Value:</td><td>${float(props.get('total_value', 0)):,.2f}</td></tr>
                        <tr><td>Type:</td><td>{props.get('property_type', 'N/A')}</td></tr>
                        <tr><td>Zone:</td><td>{props.get('zone_name', 'N/A')}</td></tr>
                    </table>
                    <hr>
                    <h4>Additional Information</h4>
                    <table style="width:100%">
                        <tr><td>Last Sale:</td><td>{props.get('last_sale_date', 'N/A')}</td></tr>
                        <tr><td>Land Use:</td><td>{props.get('land_use_description', 'N/A')}</td></tr>
                        <tr><td>Flood Zone:</td><td>{props.get('flood_zone', 'N/A')}</td></tr>
                    </table>
                </div>
            """

        except Exception as e:
            self.logger.error(f"Error creating detailed popup: {str(e)}")
            return "Error displaying information"

    def _get_property_icon(self, props: Dict) -> folium.Icon:
        """Get appropriate icon for property type"""
        try:
            icon_map = {
                'residential': 'home',
                'commercial': 'building',
                'industrial': 'industry',
                'vacant': 'square',
                'agricultural': 'leaf'
            }

            property_type = props.get('property_type', '').lower()
            icon_name = icon_map.get(property_type, 'info-sign')

            return folium.Icon(
                icon=icon_name,
                prefix='fa',
                color=self._get_icon_color(props)
            )

        except Exception as e:
            self.logger.error(f"Error getting property icon: {str(e)}")
            return folium.Icon(icon='info-sign')

    def _get_icon_color(self, props: Dict) -> str:
        """Get color based on property attributes"""
        try:
            if props.get('score', 0) >= 0.8:
                return 'green'
            elif props.get('score', 0) >= 0.5:
                return 'orange'
            return 'red'

        except Exception as e:
            self.logger.error(f"Error getting icon color: {str(e)}")
            return 'blue'

    def _create_time_entry(self, items: List[Dict]) -> Dict:
        """Create time slider entry for items"""
        try:
            entry = {}
            for item in items:
                if 'geometry' in item:
                    coords = json.dumps(item['geometry']['coordinates'][0])
                    entry[coords] = {
                        'color': self._get_icon_color(item.get('properties', {})),
                        'opacity': 0.7
                    }
            return entry

        except Exception as e:
            self.logger.error(f"Error creating time entry: {str(e)}")
            return {}
