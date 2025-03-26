"""
Interactive map visualization tool
"""
import logging
from typing import Dict, List
import folium
from folium import plugins
import geopandas as gpd
import json
import branca.colormap as cm
from pathlib import Path

class MapVisualizer:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.output_dir = Path(__file__).parent.parent.parent / 'output' / 'maps'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def create_map(self, data: List[Dict], center: tuple = None, 
                  score_field: str = None, filters: Dict = None) -> str:
        """
        Create interactive map with property data
        
        Args:
            data: List of property data with geometries
            center: Optional (lat, lon) for map center
            score_field: Field to use for color coding
            filters: Dictionary of filters to apply
            
        Returns:
            Path to generated HTML file
        """
        try:
            # Create base map
            if center:
                m = folium.Map(location=center, zoom_start=13)
            else:
                # Calculate center from data
                bounds = self._calculate_bounds(data)
                center = [(bounds[0] + bounds[2])/2, (bounds[1] + bounds[3])/2]
                m = folium.Map(location=center, zoom_start=13)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Create feature groups
            properties_group = folium.FeatureGroup(name="Properties")
            scores_group = folium.FeatureGroup(name="Scores")
            
            # Create color scale if score field provided
            if score_field:
                colormap = self._create_colormap(data, score_field)
            
            # Add properties to map
            for item in data:
                if filters and not self._passes_filters(item, filters):
                    continue
                
                # Create property polygon
                if 'geometry' in item:
                    polygon = folium.GeoJson(
                        item['geometry'],
                        style_function=lambda x: {
                            'fillColor': self._get_color(item, score_field, colormap) if score_field else '#3388ff',
                            'color': '#000000',
                            'weight': 1,
                            'fillOpacity': 0.7
                        },
                        popup=self._create_popup(item)
                    )
                    
                    # Add to appropriate group
                    if score_field:
                        polygon.add_to(scores_group)
                    else:
                        polygon.add_to(properties_group)
            
            # Add feature groups to map
            properties_group.add_to(m)
            if score_field:
                scores_group.add_to(m)
                colormap.add_to(m)
            
            # Add search control
            properties = [(item.get('properties', {}).get('address', ''), 
                         item.get('geometry', {}).get('coordinates', [])[0][0])
                        for item in data]
            search = plugins.Search(
                layer=properties_group,
                geom_type='Point',
                placeholder='Search properties',
                collapsed=False,
                search_label='address'
            ).add_to(m)
            
            # Add fullscreen control
            plugins.Fullscreen().add_to(m)
            
            # Add measure control
            plugins.MeasureControl().add_to(m)
            
            # Save map
            output_file = self.output_dir / 'property_map.html'
            m.save(str(output_file))
            
            return str(output_file)
            
        except Exception as e:
            self.logger.error(f"Error creating map: {str(e)}")
            return None
    
    def _calculate_bounds(self, data: List[Dict]) -> tuple:
        """Calculate bounds from data"""
        try:
            lats = []
            lons = []
            
            for item in data:
                if 'geometry' in item:
                    coords = item['geometry'].get('coordinates', [[]])[0]
                    lats.extend([c[1] for c in coords])
                    lons.extend([c[0] for c in coords])
            
            if lats and lons:
                return (min(lats), min(lons), max(lats), max(lons))
            return (0, 0, 0, 0)
            
        except Exception as e:
            self.logger.error(f"Error calculating bounds: {str(e)}")
            return (0, 0, 0, 0)
    
    def _create_colormap(self, data: List[Dict], score_field: str) -> cm.LinearColormap:
        """Create color map for scores"""
        try:
            scores = [self._get_nested_value(item, score_field) for item in data]
            scores = [s for s in scores if s is not None]
            
            if scores:
                return cm.LinearColormap(
                    colors=['red', 'yellow', 'green'],
                    vmin=min(scores),
                    vmax=max(scores)
                )
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating colormap: {str(e)}")
            return None
    
    def _create_popup(self, item: Dict) -> folium.Popup:
        """Create popup with property information"""
        try:
            props = item.get('properties', {})
            
            html = """
                <div style="width:200px">
                    <h4>{address}</h4>
                    <p>Owner: {owner}</p>
                    <p>Value: ${value:,.2f}</p>
                    <p>Type: {type}</p>
                    {extra_info}
                </div>
            """.format(
                address=props.get('address', 'N/A'),
                owner=props.get('owner_name', 'N/A'),
                value=float(props.get('total_value', 0)),
                type=props.get('property_type', 'N/A'),
                extra_info=self._format_extra_info(props)
            )
            
            return folium.Popup(html, max_width=300)
            
        except Exception as e:
            self.logger.error(f"Error creating popup: {str(e)}")
            return folium.Popup("Error displaying information")
    
    def _format_extra_info(self, props: Dict) -> str:
        """Format additional property information"""
        try:
            extra_info = ""
            
            if 'score' in props:
                extra_info += f"<p>Score: {props['score']:.2f}</p>"
            
            if 'occupation_type' in props:
                extra_info += f"<p>Type: {props['occupation_type']}</p>"
            
            if 'last_sale_date' in props:
                extra_info += f"<p>Last Sale: {props['last_sale_date']}</p>"
            
            return extra_info
            
        except Exception as e:
            self.logger.error(f"Error formatting extra info: {str(e)}")
            return ""
    
    def _passes_filters(self, item: Dict, filters: Dict) -> bool:
        """Check if item passes all filters"""
        try:
            for field, value in filters.items():
                item_value = self._get_nested_value(item, field)
                if item_value != value:
                    return False
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying filters: {str(e)}")
            return False
    
    def _get_nested_value(self, item: Dict, field: str) -> any:
        """Get value from nested dictionary using dot notation"""
        try:
            parts = field.split('.')
            value = item
            for part in parts:
                value = value.get(part, {})
            return value if value != {} else None
            
        except Exception as e:
            self.logger.error(f"Error getting nested value: {str(e)}")
            return None
    
    def _get_color(self, item: Dict, score_field: str, colormap: cm.LinearColormap) -> str:
        """Get color for score"""
        try:
            score = self._get_nested_value(item, score_field)
            if score is not None and colormap:
                return colormap(score)
            return '#3388ff'
            
        except Exception as e:
            self.logger.error(f"Error getting color: {str(e)}")
            return '#3388ff'
