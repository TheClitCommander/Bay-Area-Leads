"""
Collector for GIS and interactive map data
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import requests
import geopandas as gpd
import json
from shapely.geometry import Point, Polygon
from .base_collector import BaseCollector
from ..services.db_service import DatabaseService

class GISCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.db_service = DatabaseService()
        self.raw_data_path = Path(__file__).parent.parent.parent / 'data' / 'raw_files' / 'gis'
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        
    def collect(self, town: str, layer_types: List[str] = None) -> Dict:
        """
        Collect GIS data from interactive maps
        
        Args:
            town: Name of town
            layer_types: Types of layers to collect (zoning, parcels, etc.)
        """
        try:
            self.logger.info(f"Collecting GIS data for {town}")
            
            metadata = {
                'town': town,
                'collection_date': datetime.now().isoformat(),
                'layer_types': layer_types
            }
            
            # Collect different types of GIS data
            parcel_data = self._collect_parcel_data(town)
            zoning_data = self._collect_zoning_data(town)
            flood_data = self._collect_flood_data(town)
            
            # Combine all GIS data
            gis_data = {
                'parcels': parcel_data,
                'zoning': zoning_data,
                'flood_zones': flood_data
            }
            
            # Save raw data
            self._save_raw_data(town, gis_data)
            
            return {
                'success': True,
                'data': gis_data,
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error(f"Error collecting GIS data: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'metadata': metadata
            }
    
    def _collect_parcel_data(self, town: str) -> List[Dict]:
        """Collect parcel boundary and attribute data"""
        try:
            # Handle different GIS systems
            if self._is_arcgis(town):
                return self._collect_from_arcgis(town, 'parcels')
            elif self._is_qgis(town):
                return self._collect_from_qgis(town, 'parcels')
            else:
                return self._collect_from_generic_gis(town, 'parcels')
        except Exception as e:
            self.logger.error(f"Error collecting parcel data: {str(e)}")
            return []
    
    def _collect_zoning_data(self, town: str) -> List[Dict]:
        """Collect zoning boundaries and regulations"""
        try:
            if self._is_arcgis(town):
                return self._collect_from_arcgis(town, 'zoning')
            elif self._is_qgis(town):
                return self._collect_from_qgis(town, 'zoning')
            else:
                return self._collect_from_generic_gis(town, 'zoning')
        except Exception as e:
            self.logger.error(f"Error collecting zoning data: {str(e)}")
            return []
    
    def _collect_flood_data(self, town: str) -> List[Dict]:
        """Collect flood zone boundaries"""
        try:
            if self._is_arcgis(town):
                return self._collect_from_arcgis(town, 'flood')
            elif self._is_qgis(town):
                return self._collect_from_qgis(town, 'flood')
            else:
                return self._collect_from_generic_gis(town, 'flood')
        except Exception as e:
            self.logger.error(f"Error collecting flood data: {str(e)}")
            return []
    
    def _is_arcgis(self, town: str) -> bool:
        """Check if town uses ArcGIS"""
        # Will check URL patterns and API endpoints
        return False
    
    def _is_qgis(self, town: str) -> bool:
        """Check if town uses QGIS"""
        # Will check URL patterns and API endpoints
        return False
    
    def _collect_from_arcgis(self, town: str, layer_type: str) -> List[Dict]:
        """Collect data from ArcGIS server"""
        try:
            # Example ArcGIS REST API call
            # Will implement actual API calls based on town's endpoints
            api_url = f"https://{town}.maps.arcgis.com/rest/services/{layer_type}/MapServer"
            
            # Get layer info
            response = requests.get(f"{api_url}?f=json")
            layer_info = response.json()
            
            # Get features
            features_url = f"{api_url}/0/query"
            params = {
                'where': '1=1',
                'outFields': '*',
                'returnGeometry': 'true',
                'f': 'geojson'
            }
            
            response = requests.get(features_url, params=params)
            features = response.json()
            
            return self._process_geojson(features)
            
        except Exception as e:
            self.logger.error(f"Error collecting from ArcGIS: {str(e)}")
            return []
    
    def _collect_from_qgis(self, town: str, layer_type: str) -> List[Dict]:
        """Collect data from QGIS server"""
        try:
            # Example QGIS Server WFS request
            # Will implement actual WFS calls based on town's endpoints
            api_url = f"https://{town}.maps.qgis.com/wfs"
            
            params = {
                'SERVICE': 'WFS',
                'VERSION': '2.0.0',
                'REQUEST': 'GetFeature',
                'TYPENAME': layer_type,
                'OUTPUTFORMAT': 'application/json'
            }
            
            response = requests.get(api_url, params=params)
            features = response.json()
            
            return self._process_geojson(features)
            
        except Exception as e:
            self.logger.error(f"Error collecting from QGIS: {str(e)}")
            return []
    
    def _collect_from_generic_gis(self, town: str, layer_type: str) -> List[Dict]:
        """Collect data from other GIS servers"""
        try:
            # Will implement based on specific GIS system
            return []
        except Exception as e:
            self.logger.error(f"Error collecting from generic GIS: {str(e)}")
            return []
    
    def _process_geojson(self, geojson_data: Dict) -> List[Dict]:
        """Process GeoJSON data into structured format"""
        try:
            results = []
            
            for feature in geojson_data.get('features', []):
                # Extract properties
                properties = feature.get('properties', {})
                
                # Extract geometry
                geometry = feature.get('geometry', {})
                
                # Combine into result
                result = {
                    'properties': properties,
                    'geometry_type': geometry.get('type'),
                    'coordinates': geometry.get('coordinates'),
                }
                
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing GeoJSON: {str(e)}")
            return []
