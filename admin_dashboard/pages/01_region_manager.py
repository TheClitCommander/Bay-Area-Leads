"""
Region Manager - MidcoastLeads Admin Dashboard

This page provides tools for managing map-based region selections,
visualizing property distributions, and analyzing region performance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import map selection manager when available
# from cascade_plugins.map_selection.selection_manager import MapSelectionManager

# Set page config
st.set_page_config(
    page_title="Region Manager - MidcoastLeads Admin",
    page_icon="🗺️",
    layout="wide"
)

# Page styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #dee2e6;
    }
    .region-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    }
</style>
""", unsafe_allow_html=True)

def load_sample_data():
    """
    Load sample data for demonstration purposes.
    In production, this would connect to the actual map selection database.
    """
    # Sample regions data
    regions = [
        {
            'region_id': 'REG_001',
            'name': 'Downtown Brunswick',
            'description': 'Historic downtown area with mixed commercial and residential',
            'property_count': 37,
            'avg_ml_score': 78.2,
            'avg_property_value': 285000,
            'created_date': '2025-01-15',
            'coordinates': [  # Simplified polygon coordinates
                [-69.9656, 43.9145],
                [-69.9601, 43.9145],
                [-69.9601, 43.9095],
                [-69.9656, 43.9095],
                [-69.9656, 43.9145]
            ]
        },
        {
            'region_id': 'REG_002',
            'name': 'Topsham Heights',
            'description': 'Newer development area with high-value properties',
            'property_count': 42,
            'avg_ml_score': 82.7,
            'avg_property_value': 342000,
            'created_date': '2025-02-03',
            'coordinates': [  # Simplified polygon coordinates
                [-69.9756, 43.9245],
                [-69.9701, 43.9245],
                [-69.9701, 43.9195],
                [-69.9756, 43.9195],
                [-69.9756, 43.9245]
            ]
        },
        {
            'region_id': 'REG_003',
            'name': 'Coastal Area',
            'description': 'Waterfront properties with investment potential',
            'property_count': 21,
            'avg_ml_score': 85.1,
            'avg_property_value': 425000,
            'created_date': '2025-02-27',
            'coordinates': [  # Simplified polygon coordinates
                [-69.9856, 43.9345],
                [-69.9801, 43.9345],
                [-69.9801, 43.9295],
                [-69.9856, 43.9295],
                [-69.9856, 43.9345]
            ]
        }
    ]
    
    # Sample properties data
    properties = []
    for i in range(100):
        # Generate random property with coordinates within one of the regions
        region_idx = np.random.randint(0, 3)
        region = regions[region_idx]
        
        # Random coordinates within the region
        min_lon = min(coord[0] for coord in region['coordinates'])
        max_lon = max(coord[0] for coord in region['coordinates'])
        min_lat = min(coord[1] for coord in region['coordinates'])
        max_lat = max(coord[1] for coord in region['coordinates'])
        
        lon = np.random.uniform(min_lon, max_lon)
        lat = np.random.uniform(min_lat, max_lat)
        
        year_built = np.random.randint(1920, 2020)
        sq_ft = np.random.randint(1000, 3500)
        prop = {
            'property_id': f'PROP_{i:04d}',
            'address': f'{i+100} Main St, Brunswick, ME',
            'value': np.random.randint(200000, 500000),
            'assessed_value': np.random.randint(180000, 450000),
            'year_built': year_built,
            'sq_ft': sq_ft,
            'acres': round(np.random.uniform(0.2, 2.0), 2),
            'bedrooms': np.random.randint(2, 6),
            'bathrooms': np.random.randint(1, 4),
            'property_type': np.random.choice(['single_family', 'multi_family', 'condo', 'commercial']),
            'zoning': np.random.choice(['residential', 'commercial', 'mixed', 'industrial']),
            'ml_score': round(np.random.uniform(40, 95), 1),
            'region_id': region['region_id'],
            'longitude': lon,
            'latitude': lat
        }
        properties.append(prop)
    
    return {
        'regions': regions,
        'properties': properties
    }

def create_map_visualization(regions, properties):
    """Create an interactive map with regions and properties"""
    # Create property distribution map
    fig = go.Figure()
    
    # Add properties as scatter points
    prop_df = pd.DataFrame(properties)
    
    # Color by ML score
    fig.add_trace(go.Scattermapbox(
        lat=prop_df['latitude'],
        lon=prop_df['longitude'],
        mode='markers',
        marker=dict(
            size=8,
            color=prop_df['ml_score'],
            colorscale='Viridis',
            colorbar=dict(title='ML Score'),
            opacity=0.7
        ),
        text=prop_df.apply(lambda x: f"{x['property_id']}<br>{x['address']}<br>Value: ${x['value']:,}<br>ML Score: {x['ml_score']}", axis=1),
        hoverinfo='text',
        name='Properties'
    ))
    
    # Add region polygons
    for region in regions:
        coords = region['coordinates']
        lons = [coord[0] for coord in coords]
        lats = [coord[1] for coord in coords]
        
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='lines',
            line=dict(width=2, color='red'),
            fill='toself',
            fillcolor='rgba(255, 0, 0, 0.1)',
            name=region['name'],
            text=f"{region['name']}<br>{region['description']}<br>Properties: {region['property_count']}<br>Avg ML Score: {region['avg_ml_score']}",
            hoverinfo='text'
        ))
    
    # Update map layout
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lon=-69.97, lat=43.92),
            zoom=12
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return fig

def region_manager():
    st.markdown('<h1 class="main-header">Region Manager</h1>', unsafe_allow_html=True)
    
    # Load data
    data = load_sample_data()
    regions = data['regions']
    properties = data['properties']
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Interactive Map")
        
        # Create map
        fig = create_map_visualization(regions, properties)
        st.plotly_chart(fig, use_container_width=True)
        
        # Map controls
        st.markdown("### Map Controls")
        control_col1, control_col2, control_col3 = st.columns(3)
        
        with control_col1:
            if st.button("Create New Region"):
                st.session_state.show_drawing_tools = True
                st.info("In production, this would activate the drawing tools.")
                
        with control_col2:
            if st.button("Export Properties"):
                st.info("This would export properties from selected regions.")
                
        with control_col3:
            if st.button("Generate Region Report"):
                st.info("This would trigger report generation for selected regions.")
                
        # Optional drawing tools
        if st.session_state.get('show_drawing_tools', False):
            st.markdown("### Drawing Tools")
            st.info("In production, this would integrate with the Streamlit Drawing Canvas component.")
            
            # Placeholder for drawing tools
            col1, col2, col3 = st.columns(3)
            with col1:
                st.selectbox("Drawing Type", ["Polygon", "Rectangle", "Freeform"])
            with col2:
                st.color_picker("Line Color", "#FF0000")
            with col3:
                st.slider("Line Width", 1, 10, 3)
                
    with col2:
        st.markdown("### Region Details")
        
        # Region selection
        selected_region_name = st.selectbox("Select Region", [r['name'] for r in regions])
        selected_region = next((r for r in regions if r['name'] == selected_region_name), None)
        
        if selected_region:
            # Region stats
            st.markdown(f"**Region ID:** {selected_region['region_id']}")
            st.markdown(f"**Created:** {selected_region['created_date']}")
            st.markdown(f"**Description:** {selected_region['description']}")
            
            # Metrics
            st.metric("Property Count", selected_region['property_count'])
            st.metric("Average ML Score", selected_region['avg_ml_score'])
            st.metric("Average Property Value", f"${selected_region['avg_property_value']:,}")
            
            # Actions
            if st.button("Edit Region"):
                st.info("This would open region editing tools.")
                
            if st.button("Delete Region"):
                st.warning("This would prompt for confirmation before deleting.")
            
            # Region properties
            st.markdown("### Properties in Region")
            region_properties = [p for p in properties if p.get('region_id') == selected_region['region_id']]
            region_props_df = pd.DataFrame(region_properties)[['property_id', 'address', 'ml_score', 'value']]
            st.dataframe(region_props_df, use_container_width=True, hide_index=True)
            
            # Property type distribution
            st.markdown("### Property Distribution")
            prop_types = [p['property_type'] for p in region_properties]
            prop_type_counts = pd.Series(prop_types).value_counts().reset_index()
            prop_type_counts.columns = ['Property Type', 'Count']
            
            fig = px.pie(prop_type_counts, values='Count', names='Property Type', hole=0.4)
            fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    # Initialize session state
    if 'show_drawing_tools' not in st.session_state:
        st.session_state.show_drawing_tools = False
    
    region_manager()
