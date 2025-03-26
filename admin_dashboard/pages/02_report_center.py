"""
Report Center - MidcoastLeads Admin Dashboard

This page provides an interface to generate, view, and manage property reports
using the WeasyPrint-based report generator system.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import json
import base64

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import report generator when connecting to real modules
# from cascade_plugins.packet_templates.report_generator import ReportGenerator

# Set page config
st.set_page_config(
    page_title="Report Center - MidcoastLeads Admin",
    page_icon="📊",
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
    .report-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    }
    .pdf-preview {
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

def load_sample_data():
    """
    Load sample data for demonstration purposes.
    In production, this would connect to the actual database.
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
            'ml_score': round(np.random.uniform(40, 95), 1)
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
    
    # Sample reports data with absolute paths
    reports = [
        {
            'report_id': 'RPT_001',
            'title': 'Downtown Brunswick Portfolio',
            'region_id': 'REG_001',
            'property_count': 5,
            'created_date': '2025-03-01',
            'status': 'completed',
            'file_path': '/Users/bendickinson/Desktop/MidcoastLeads/cascade_plugins/packet_templates/output/multi_property_report_20250326.pdf'
        },
        {
            'report_id': 'RPT_002',
            'title': '123 Main St Property Analysis',
            'property_id': 'PROP_0001',
            'created_date': '2025-03-10',
            'status': 'completed',
            'file_path': '/Users/bendickinson/Desktop/MidcoastLeads/cascade_plugins/packet_templates/output/property_report_PROP_0001_123_Main_St,_Brunswick,_ME_20250326.pdf'
        },
        {
            'report_id': 'RPT_003',
            'title': 'Topsham Investment Opportunities',
            'region_id': 'REG_002',
            'property_count': 8,
            'created_date': '2025-03-15',
            'status': 'completed',
            'file_path': '/Users/bendickinson/Desktop/MidcoastLeads/cascade_plugins/packet_templates/output/multi_property_report_20250326.pdf'
        }
    ]
    
    # Sample branding profiles
    branding_profiles = [
        {
            'profile_id': 'BRAND_001',
            'name': 'Midcoast Leads (Default)',
            'primary_color': '#1E88E5',
            'secondary_color': '#26A69A',
            'logo_path': '/static/logo.png',
            'header_style': 'standard',
            'font_family': 'Roboto, sans-serif'
        },
        {
            'profile_id': 'BRAND_002',
            'name': 'Brunswick Investments',
            'primary_color': '#3949AB',
            'secondary_color': '#43A047',
            'logo_path': '/static/brunswick_logo.png',
            'header_style': 'minimal',
            'font_family': 'Montserrat, sans-serif'
        },
        {
            'profile_id': 'BRAND_003',
            'name': 'Maine Coastal Properties',
            'primary_color': '#00796B',
            'secondary_color': '#FF5722',
            'logo_path': '/static/coastal_logo.png',
            'header_style': 'elegant',
            'font_family': 'Lato, sans-serif'
        }
    ]
    
    return {
        'properties': properties,
        'regions': regions,
        'reports': reports,
        'branding_profiles': branding_profiles
    }

def display_pdf(file_path):
    """Display a PDF file in Streamlit"""
    # Check if file exists
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Embed PDF viewer
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.error(f"PDF file not found: {file_path}")

def report_center():
    st.markdown('<h1 class="main-header">Report Center</h1>', unsafe_allow_html=True)
    
    # Load data
    data = load_sample_data()
    
    # Sidebar for creation controls
    with st.sidebar:
        st.header("Report Generator")
        report_type = st.selectbox("Report Type", ["Single Property", "Multi-Property Portfolio", "Region Analysis"])
        
        if report_type == "Single Property":
            property_options = [f"{p['property_id']} - {p['address']}" for p in data['properties'][:10]]
            selected_property = st.selectbox("Select Property", property_options)
            include_comps = st.checkbox("Include Comparable Properties", value=True)
            num_comps = st.slider("Number of Comparables", 3, 10, 5) if include_comps else 0
            
        elif report_type == "Multi-Property Portfolio":
            region_options = [r['name'] for r in data['regions']]
            selected_region = st.selectbox("Select Region", region_options)
            max_properties = st.slider("Maximum Properties", 5, 50, 10)
            sort_by = st.selectbox("Sort Properties By", ["ML Score", "Property Value", "ROI Potential"])
            
        elif report_type == "Region Analysis":
            region_options = [r['name'] for r in data['regions']]
            selected_region = st.selectbox("Select Region", region_options)
            include_heatmap = st.checkbox("Include Value Heatmap", value=True)
            
        # Branding options
        st.header("Branding Options")
        branding_profile = st.selectbox(
            "Branding Profile", 
            [p['name'] for p in data['branding_profiles']]
        )
        
        # Advanced options
        st.header("Advanced Options")
        include_ml_details = st.checkbox("Include ML Score Details", value=True)
        include_charts = st.checkbox("Include Visualization Charts", value=True)
        
        # Generate report button
        if st.button("Generate Report", type="primary"):
            st.session_state.report_generated = True
            
            # In production, this would call the actual report generator
            # For now, we'll simulate by showing an existing report
            if report_type == "Single Property":
                st.session_state.generated_report_path = data['reports'][1]['file_path']
                st.session_state.generated_report_title = "Single Property Report Generated"
            else:
                st.session_state.generated_report_path = data['reports'][0]['file_path']
                st.session_state.generated_report_title = "Multi-Property Report Generated"
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["Generated Reports", "Report History"])
    
    with tab1:
        if st.session_state.get('report_generated', False):
            st.success(f"{st.session_state.generated_report_title} successfully!")
            
            # Add email options
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("### PDF Preview")
                display_pdf(st.session_state.generated_report_path)
                
            with col2:
                st.markdown("### Distribution Options")
                
                recipient_email = st.text_input("Recipient Email")
                include_summary = st.checkbox("Include Email Summary", value=True)
                
                if st.button("Send Report"):
                    if recipient_email:
                        st.success(f"Report sent to {recipient_email}")
                    else:
                        st.error("Please enter recipient email")
                
                if st.button("Download PDF"):
                    # This would download the PDF in production
                    st.info("In production, this would download the PDF file.")
                    
                if st.button("Save to CRM"):
                    st.success("Report saved to CRM system")
        else:
            st.info("Use the controls in the sidebar to generate a new report.")
    
    with tab2:
        st.markdown("### Previously Generated Reports")
        
        # Filter controls
        col1, col2, col3 = st.columns(3)
        with col1:
            report_filter = st.selectbox("Filter By Type", ["All Reports", "Single Property", "Multi-Property", "Region Analysis"])
        with col2:
            date_range = st.selectbox("Date Range", ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"])
        with col3:
            sort_order = st.selectbox("Sort By", ["Newest First", "Oldest First", "Title (A-Z)"])
            
        # Reports list
        for report in data['reports']:
            with st.container():
                st.markdown(f"""
                <div class="report-card">
                    <h3>{report['title']}</h3>
                    <p>Generated: {report['created_date']} | Status: {report['status']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    if st.button(f"View {report['report_id']}", key=f"view_{report['report_id']}"):
                        st.session_state.selected_report = report
                        st.session_state.show_report = True
                with col2:
                    if st.button(f"Email {report['report_id']}", key=f"email_{report['report_id']}"):
                        st.info(f"This would open email dialog for {report['title']}")
                with col3:
                    if st.button(f"Edit {report['report_id']}", key=f"edit_{report['report_id']}"):
                        st.info(f"This would open the report editor for {report['title']}")
                with col4:
                    if st.button(f"Delete {report['report_id']}", key=f"delete_{report['report_id']}"):
                        st.warning(f"This would delete {report['title']}")
        
        # Show selected report
        if st.session_state.get('show_report', False):
            st.markdown("### Report Preview")
            display_pdf(st.session_state.selected_report['file_path'])

if __name__ == "__main__":
    # Initialize session state
    if 'report_generated' not in st.session_state:
        st.session_state.report_generated = False
    if 'show_report' not in st.session_state:
        st.session_state.show_report = False
    
    report_center()
