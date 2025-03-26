"""
MidcoastLeads Admin Dashboard

This is the main entry point for the admin dashboard, providing a comprehensive
interface to manage the lead generation, analysis, and reporting system.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components (will implement proper imports when we connect real modules)
# from cascade_plugins.packet_templates.report_generator import get_report_generator
# from cascade_plugins.packet_templates.chart_generator import get_chart_generator

# Set page config
st.set_page_config(
    page_title="MidcoastLeads Admin",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
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
    """
    Load sample data for demonstration purposes.
    In production, this would connect to real databases.
    """
    # Sample properties data
    properties = []
    for i in range(100):
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
            'lead_score': round(np.random.uniform(50, 90), 1),
            'undervaluation_score': round(np.random.uniform(30, 100), 1),
            'delinquency_score': round(np.random.uniform(0, 100), 1),
            'zoning_score': round(np.random.uniform(50, 100), 1),
            'owner_score': round(np.random.uniform(40, 95), 1),
            'last_updated': (datetime.now() - pd.Timedelta(days=np.random.randint(1, 60))).strftime('%Y-%m-%d')
        }
        properties.append(prop)
    
    # Sample regions data
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
    
    # Sample reports data
    reports = [
        {
            'report_id': 'RPT_001',
            'title': 'Downtown Brunswick Portfolio',
            'region_id': 'REG_001',
            'property_count': 5,
            'created_date': '2025-03-01',
            'status': 'completed',
            'file_path': '/output/portfolio_downtown_20250301.pdf'
        },
        {
            'report_id': 'RPT_002',
            'title': '123 Main St Property Analysis',
            'property_id': 'PROP_0001',
            'created_date': '2025-03-10',
            'status': 'completed',
            'file_path': '/output/property_PROP_0001_20250310.pdf'
        },
        {
            'report_id': 'RPT_003',
            'title': 'Topsham Investment Opportunities',
            'region_id': 'REG_002',
            'property_count': 8,
            'created_date': '2025-03-15',
            'status': 'completed',
            'file_path': '/output/portfolio_topsham_20250315.pdf'
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
    st.markdown('<h1 class="main-header">MidcoastLeads Admin Dashboard</h1>', unsafe_allow_html=True)
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">100</div>
            <div class="metric-label">Total Properties</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">3</div>
            <div class="metric-label">Active Regions</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">23</div>
            <div class="metric-label">High-Value Leads</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">3</div>
            <div class="metric-label">Generated Reports</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity section
    st.markdown('<h2 class="section-header">Recent Activity</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Top Leads", "Recent Reports", "Region Performance"])
    
    with tab1:
        # Top leads by ML score
        top_leads = sorted(data['properties'], key=lambda x: x['ml_score'], reverse=True)[:10]
        top_leads_df = pd.DataFrame(top_leads)[['property_id', 'address', 'ml_score', 'value', 'property_type']]
        st.dataframe(top_leads_df, use_container_width=True, hide_index=True)
        
    with tab2:
        # Recent reports
        reports_df = pd.DataFrame(data['reports'])
        st.dataframe(reports_df, use_container_width=True, hide_index=True)
        
        if st.button("Generate New Report"):
            st.info("This would open the report generation interface in production.")
            
    with tab3:
        # Region performance
        regions_df = pd.DataFrame(data['regions'])
        st.dataframe(regions_df, use_container_width=True, hide_index=True)
        
        if st.button("Manage Regions"):
            st.info("This would open the region management interface in production.")
    
    # Quick actions
    st.markdown('<h2 class="section-header">Quick Actions</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Generate Report")
        report_type = st.selectbox("Report Type", ["Property Report", "Multi-Property Portfolio", "Region Analysis"])
        
        if report_type == "Property Report":
            property_id = st.selectbox("Select Property", [p['property_id'] + " - " + p['address'] for p in data['properties'][:10]])
        elif report_type == "Multi-Property Portfolio":
            num_properties = st.slider("Number of Properties", 2, 20, 5)
        else:
            region = st.selectbox("Select Region", [r['name'] for r in data['regions']])
            
        if st.button("Create Report", key="create_report"):
            st.success(f"Report generation initiated for {report_type}")
            
    with col2:
        st.markdown("### ML Model Control")
        st.selectbox("Model Version", ["v1.2.3 (Current)", "v1.2.2", "v1.1.0"])
        feature_importance = {
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
        
        features_df = pd.DataFrame(
            {"Feature": list(feature_importance.keys()), 
             "Importance": list(feature_importance.values())}
        ).sort_values("Importance", ascending=False)
        
        st.dataframe(features_df, use_container_width=True, hide_index=True)
        
        if st.button("Retrain Model"):
            st.info("This would trigger model retraining in production.")
            
    with col3:
        st.markdown("### System Status")
        st.metric("System Health", "Good", "+3 components online")
        st.metric("Last Data Update", "2 hours ago", "-")
        st.metric("API Status", "Online", "100% uptime")
        
        if st.button("Refresh Data"):
            st.info("This would refresh all data sources in production.")

if __name__ == "__main__":
    main()
