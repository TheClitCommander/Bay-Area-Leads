import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import plotly.express as px

# Add path for imports if needed
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set page config
st.set_page_config(
    page_title="MidcoastLeads Dashboard",
    page_icon="🏠",
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
</style>
""", unsafe_allow_html=True)

def load_sample_data():
    """Load sample data for demonstration"""
    # Sample properties
    properties = []
    for i in range(100):
        year_built = np.random.randint(1920, 2020)
        sq_ft = np.random.randint(1000, 3500)
        prop = {
            'property_id': f'PROP_{i:04d}',
            'address': f'{i+100} Main St, Brunswick, ME',
            'value': np.random.randint(200000, 500000),
            'year_built': year_built,
            'sq_ft': sq_ft,
            'acres': round(np.random.uniform(0.2, 2.0), 2),
            'bedrooms': np.random.randint(2, 6),
            'bathrooms': np.random.randint(1, 4),
            'property_type': np.random.choice(['single_family', 'multi_family', 'condo', 'commercial']),
            'zoning': np.random.choice(['residential', 'commercial', 'mixed', 'industrial']),
            'ml_score': round(np.random.uniform(40, 95), 1)
        }
        properties.append(prop)
    
    # Sample regions
    regions = [
        {
            'region_id': 'REG_001',
            'name': 'Downtown Brunswick',
            'description': 'Historic downtown area with mixed commercial and residential',
            'property_count': 37,
            'avg_ml_score': 78.2,
            'avg_property_value': 285000,
            'created_date': '2025-01-15'
        },
        {
            'region_id': 'REG_002',
            'name': 'Topsham Heights',
            'description': 'Newer development area with high-value properties',
            'property_count': 42,
            'avg_ml_score': 82.7,
            'avg_property_value': 342000,
            'created_date': '2025-02-03'
        },
        {
            'region_id': 'REG_003',
            'name': 'Coastal Area',
            'description': 'Waterfront properties with investment potential',
            'property_count': 21,
            'avg_ml_score': 85.1,
            'avg_property_value': 425000,
            'created_date': '2025-02-27'
        }
    ]
    
    # Sample reports
    reports = [
        {
            'report_id': 'RPT_001',
            'title': 'Downtown Brunswick Portfolio',
            'region_id': 'REG_001',
            'property_count': 5,
            'created_date': '2025-03-01',
            'file_path': '/Users/bendickinson/Desktop/MidcoastLeads/cascade_plugins/packet_templates/output/multi_property_report_20250326.pdf'
        },
        {
            'report_id': 'RPT_002',
            'title': '123 Main St Property Analysis',
            'property_id': 'PROP_0001',
            'created_date': '2025-03-10',
            'file_path': '/Users/bendickinson/Desktop/MidcoastLeads/cascade_plugins/packet_templates/output/property_report_PROP_0001_123_Main_St,_Brunswick,_ME_20250326.pdf'
        }
    ]
    
    return {
        'properties': properties,
        'regions': regions,
        'reports': reports
    }

def main():
    """Main dashboard function"""
    # Load data
    data = load_sample_data()
    
    # Dashboard header
    st.markdown('<h1 class="main-header">MidcoastLeads Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Region Manager", "Report Center", "ML Models"])
    
    if page == "Dashboard":
        show_dashboard(data)
    elif page == "Region Manager":
        show_region_manager(data)
    elif page == "Report Center":
        show_report_center(data)
    elif page == "ML Models":
        show_ml_models(data)

def show_dashboard(data):
    """Show main dashboard page"""
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Properties", len(data['properties']))
    with col2:
        st.metric("Active Regions", len(data['regions']))
    with col3:
        high_value_leads = len([p for p in data['properties'] if p['ml_score'] > 75])
        st.metric("High-Value Leads", high_value_leads)
    with col4:
        st.metric("Generated Reports", len(data['reports']))
    
    # Charts
    st.subheader("Property Value Distribution")
    values = [p['value'] for p in data['properties']]
    fig = px.histogram(values, nbins=20)
    st.plotly_chart(fig, use_container_width=True)
    
    # Top leads
    st.subheader("Top Leads by ML Score")
    top_leads = sorted(data['properties'], key=lambda x: x['ml_score'], reverse=True)[:10]
    top_leads_df = pd.DataFrame(top_leads)[['property_id', 'address', 'ml_score', 'value', 'property_type']]
    st.dataframe(top_leads_df, use_container_width=True)

def show_region_manager(data):
    """Show region manager page"""
    st.subheader("Region Manager")
    st.write("This would integrate with our map-based selection system")
    
    # Display regions
    for region in data['regions']:
        st.markdown(f"### {region['name']}")
        st.write(f"Description: {region['description']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Properties", region['property_count'])
        with col2:
            st.metric("Avg ML Score", region['avg_ml_score'])
        with col3:
            st.metric("Avg Value", f"${region['avg_property_value']:,}")
    
    # Map placeholder
    st.info("In full implementation, this would show our interactive map with drawable regions")

def show_report_center(data):
    """Show report center page"""
    st.subheader("Report Center")
    
    # Report generation form
    st.markdown("### Generate New Report")
    report_type = st.selectbox("Report Type", ["Single Property", "Multi-Property Portfolio"])
    
    if report_type == "Single Property":
        property_id = st.selectbox("Select Property", 
                                [f"{p['property_id']} - {p['address']}" for p in data['properties'][:10]])
    else:
        region = st.selectbox("Select Region", [r['name'] for r in data['regions']])
    
    if st.button("Generate Report"):
        st.success("Report generated successfully!")
        st.info("This would connect to our WeasyPrint report generator")
    
    # Existing reports
    st.markdown("### Existing Reports")
    for report in data['reports']:
        st.markdown(f"**{report['title']}** - Generated: {report['created_date']}")
        
        if os.path.exists(report['file_path']):
            if st.button(f"View {report['report_id']}", key=f"view_{report['report_id']}"):
                st.info(f"This would open {report['file_path']}")

def show_ml_models(data):
    """Show ML models page"""
    st.subheader("ML Model Management")
    
    # Feature importance chart
    st.markdown("### Feature Importance")
    features = {
        "Year Built": 0.15,
        "Square Feet": 0.12,
        "Acres": 0.05,
        "Bedrooms": 0.08,
        "Bathrooms": 0.06,
        "Property Type": 0.18,
        "Zoning": 0.22,
        "Value": 0.07,
        "Assessed Value": 0.05
    }
    
    fig = px.bar(
        x=list(features.values()),
        y=list(features.keys()),
        orientation='h',
        labels={'x': 'Importance', 'y': 'Feature'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Model retraining
    st.markdown("### Model Training")
    col1, col2 = st.columns(2)
    
    with col1:
        model_type = st.selectbox("Model Type", ["Random Forest", "XGBoost", "Gradient Boosting"])
    
    with col2:
        data_split = st.slider("Training/Test Split", 60, 90, 80, 5)
    
    if st.button("Train Model"):
        st.info("This would connect to our ML training pipeline")
        
        with st.spinner("Training model..."):
            # Simulate training process
            progress = st.progress(0)
            for i in range(100):
                progress.progress(i + 1)
            
            st.success("Model trained successfully!")

if __name__ == "__main__":
    main()
