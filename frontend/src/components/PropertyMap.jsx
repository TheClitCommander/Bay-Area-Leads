import React, { useRef, useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

// Components
import PropertyPreview from './PropertyPreview';
import MapControls from './MapControls';

// Hooks
import useMapBounds from '../hooks/useMapBounds';
import useFilters from '../hooks/useFilters';

function PropertyMap() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const { bounds } = useMapBounds();
  const { filters } = useFilters();
  
  // Fetch properties in view
  const { data } = useQuery(
    ['map-properties', bounds, filters],
    () => fetch(`/api/map/properties?bounds=${bounds}`).then(res => res.json())
  );
  
  useEffect(() => {
    if (!map.current) {
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v11',
        center: [-69.9653, 43.9145], // Brunswick, ME
        zoom: 13
      });
      
      // Add controls
      map.current.addControl(new mapboxgl.NavigationControl());
      map.current.addControl(new mapboxgl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true
      }));
    }
  }, []);
  
  // Update markers when data changes
  useEffect(() => {
    if (!data?.properties) return;
    
    // Remove existing markers
    document.querySelectorAll('.mapboxgl-marker').forEach(el => el.remove());
    
    // Add new markers
    data.properties.forEach(property => {
      const el = document.createElement('div');
      el.className = 'marker';
      
      // Style marker based on score
      if (property.score > 0.8) {
        el.classList.add('marker-high');
      } else if (property.score > 0.6) {
        el.classList.add('marker-medium');
      } else {
        el.classList.add('marker-low');
      }
      
      // Add marker to map
      new mapboxgl.Marker(el)
        .setLngLat([property.longitude, property.latitude])
        .addTo(map.current);
        
      // Add click handler
      el.addEventListener('click', () => {
        setSelectedProperty(property);
      });
    });
  }, [data]);
  
  return (
    <div className="relative h-full">
      {/* Map Container */}
      <div 
        ref={mapContainer} 
        className="absolute inset-0"
      />
      
      {/* Map Controls */}
      <MapControls
        className="absolute top-4 right-4"
        onViewChange={() => {}}
        onFilterChange={() => {}}
      />
      
      {/* Property Preview */}
      {selectedProperty && (
        <PropertyPreview
          property={selectedProperty}
          className="absolute bottom-4 left-4 w-80"
          onClose={() => setSelectedProperty(null)}
        />
      )}
      
      {/* Heatmap Toggle */}
      <button
        className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-2"
        onClick={() => {/* toggle heatmap */}}
      >
        Toggle Heatmap
      </button>
    </div>
  );
}

export default PropertyMap;
