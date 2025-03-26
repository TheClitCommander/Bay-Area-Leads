"""
ML Control Panel - MidcoastLeads Admin Dashboard

This page provides tools for managing machine learning models,
including training, evaluation, feature importance analysis,
and monitoring prediction performance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime, timedelta
import json
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import ML model when available
# from src.ml.lead_prediction_model import LeadPredictionModel

# Set page config
st.set_page_config(
    page_title="ML Control Panel - MidcoastLeads Admin",
    page_icon="🧠",
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
    .model-card {
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    }
    .feature-bar {
        height: 25px;
        border-radius: 3px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

def load_sample_ml_data():
    """
    Load sample ML data for demonstration purposes.
    In production, this would connect to the actual ML model.
    """
    # Sample ML models
    models = [
        {
            'model_id': 'ML_001',
            'name': 'Lead Prediction v1.2.3',
            'type': 'Random Forest',
            'status': 'active',
            'accuracy': 0.87,
            'precision': 0.82,
            'recall': 0.79,
            'f1_score': 0.80,
            'created_date': '2025-02-15',
            'last_trained': '2025-03-20',
            'description': 'Production model for lead scoring'
        },
        {
            'model_id': 'ML_002',
            'name': 'Lead Prediction v1.2.2',
            'type': 'Random Forest',
            'status': 'archived',
            'accuracy': 0.85,
            'precision': 0.81,
            'recall': 0.77,
            'f1_score': 0.79,
            'created_date': '2025-01-20',
            'last_trained': '2025-02-10',
            'description': 'Previous production model'
        },
        {
            'model_id': 'ML_003',
            'name': 'Experimental XGBoost Model',
            'type': 'XGBoost',
            'status': 'experimental',
            'accuracy': 0.89,
            'precision': 0.83,
            'recall': 0.81,
            'f1_score': 0.82,
            'created_date': '2025-03-10',
            'last_trained': '2025-03-15',
            'description': 'Testing XGBoost performance against Random Forest'
        }
    ]
    
    # Feature importance data
    feature_importance = {
        'ML_001': {
            'Year Built': 0.15,
            'Square Feet': 0.12,
            'Acres': 0.05,
            'Bedrooms': 0.08,
            'Bathrooms': 0.06,
            'Property Type': 0.18,
            'Zoning': 0.22,
            'Value': 0.07,
            'Assessed Value': 0.05,
            'Tax Rate': 0.02
        },
        'ML_002': {
            'Year Built': 0.16,
            'Square Feet': 0.11,
            'Acres': 0.06,
            'Bedrooms': 0.09,
            'Bathrooms': 0.05,
            'Property Type': 0.17,
            'Zoning': 0.21,
            'Value': 0.08,
            'Assessed Value': 0.04,
            'Tax Rate': 0.03
        },
        'ML_003': {
            'Year Built': 0.14,
            'Square Feet': 0.13,
            'Acres': 0.04,
            'Bedrooms': 0.07,
            'Bathrooms': 0.06,
            'Property Type': 0.19,
            'Zoning': 0.24,
            'Value': 0.06,
            'Assessed Value': 0.05,
            'Tax Rate': 0.02
        }
    }
    
    # Generate prediction history data
    prediction_history = []
    start_date = datetime.now() - timedelta(days=60)
    
    for i in range(60):
        date = start_date + timedelta(days=i)
        accuracy = 0.82 + (i * 0.001) + (random.random() * 0.02 - 0.01)
        precision = 0.79 + (i * 0.0008) + (random.random() * 0.02 - 0.01)
        recall = 0.76 + (i * 0.0012) + (random.random() * 0.02 - 0.01)
        
        prediction_history.append({
            'date': date.strftime('%Y-%m-%d'),
            'accuracy': round(min(accuracy, 1.0), 3),
            'precision': round(min(precision, 1.0), 3),
            'recall': round(min(recall, 1.0), 3),
            'lead_count': random.randint(10, 50)
        })
    
    return {
        'models': models,
        'feature_importance': feature_importance,
        'prediction_history': prediction_history
    }

def create_feature_importance_chart(feature_importance):
    """Create a bar chart visualizing feature importance"""
    df = pd.DataFrame({
        'Feature': list(feature_importance.keys()),
        'Importance': list(feature_importance.values())
    }).sort_values('Importance', ascending=False)
    
    fig = px.bar(
        df, 
        x='Importance', 
        y='Feature',
        orientation='h',
        color='Importance',
        color_continuous_scale='Viridis',
        labels={'Importance': 'Feature Importance', 'Feature': ''},
        title='Feature Importance'
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=50, b=10),
        coloraxis_showscale=False
    )
    
    return fig

def create_performance_history_chart(prediction_history):
    """Create a line chart visualizing model performance over time"""
    df = pd.DataFrame(prediction_history)
    df['date'] = pd.to_datetime(df['date'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['accuracy'],
        mode='lines',
        name='Accuracy',
        line=dict(color='#2962FF', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['precision'],
        mode='lines',
        name='Precision',
        line=dict(color='#00C853', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['recall'],
        mode='lines',
        name='Recall',
        line=dict(color='#FF6D00', width=2)
    ))
    
    fig.update_layout(
        title='Model Performance History',
        xaxis_title='Date',
        yaxis_title='Score',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=10, r=10, t=50, b=10),
        height=350
    )
    
    return fig

def create_lead_distribution_chart():
    """Create a histogram of lead score distribution"""
    # Generate sample lead scores
    np.random.seed(42)
    scores = np.random.beta(5, 2, size=1000) * 100
    
    fig = px.histogram(
        scores, 
        nbins=20,
        labels={'value': 'Lead Score', 'count': 'Number of Properties'},
        title='Lead Score Distribution',
        color_discrete_sequence=['#3949AB']
    )
    
    fig.update_layout(
        xaxis_title='Lead Score',
        yaxis_title='Number of Properties',
        margin=dict(l=10, r=10, t=50, b=10),
        height=300
    )
    
    return fig

def ml_control_panel():
    st.markdown('<h1 class="main-header">ML Control Panel</h1>', unsafe_allow_html=True)
    
    # Load data
    data = load_sample_ml_data()
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["Model Dashboard", "Training & Evaluation", "Feature Analysis"])
    
    with tab1:
        # Model selection
        active_model = next((m for m in data['models'] if m['status'] == 'active'), data['models'][0])
        
        # Model status card
        st.markdown('<h2 class="section-header">Current Model Status</h2>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Active Model", active_model['name'])
        with col2:
            st.metric("Accuracy", f"{active_model['accuracy']:.2f}")
        with col3:
            st.metric("Precision", f"{active_model['precision']:.2f}")
        with col4:
            st.metric("Recall", f"{active_model['recall']:.2f}")
        
        st.markdown('<h2 class="section-header">Performance History</h2>', unsafe_allow_html=True)
        
        # Performance history chart
        fig = create_performance_history_chart(data['prediction_history'])
        st.plotly_chart(fig, use_container_width=True)
        
        # Lead score distribution
        st.markdown('<h2 class="section-header">Lead Score Distribution</h2>', unsafe_allow_html=True)
        
        # Lead distribution chart
        fig = create_lead_distribution_chart()
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent predictions
        st.markdown('<h2 class="section-header">Recent Predictions</h2>', unsafe_allow_html=True)
        
        # Generate sample recent predictions
        recent_predictions = []
        for i in range(10):
            score = round(random.uniform(50, 95), 1)
            recent_predictions.append({
                'property_id': f'PROP_{i:04d}',
                'address': f'{i+100} Main St, Brunswick, ME',
                'prediction_date': (datetime.now() - timedelta(days=random.randint(0, 5))).strftime('%Y-%m-%d'),
                'lead_score': score,
                'confidence': round(random.uniform(0.7, 0.95), 2)
            })
        
        predictions_df = pd.DataFrame(recent_predictions)
        st.dataframe(predictions_df, use_container_width=True, hide_index=True)
    
    with tab2:
        # Training controls
        st.markdown('<h2 class="section-header">Training Controls</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Configuration")
            
            model_type = st.selectbox("Model Type", ["Random Forest", "XGBoost", "Gradient Boosting", "Neural Network"])
            data_split = st.slider("Training/Test Split", 60, 90, 80, 5)
            include_features = st.multiselect(
                "Features to Include",
                ["Year Built", "Square Feet", "Acres", "Bedrooms", "Bathrooms", 
                 "Property Type", "Zoning", "Value", "Assessed Value", "Tax Rate"],
                ["Year Built", "Square Feet", "Acres", "Bedrooms", "Bathrooms", 
                 "Property Type", "Zoning", "Value", "Assessed Value"]
            )
            
            hyperparams = st.checkbox("Configure Hyperparameters", value=False)
            
            if hyperparams:
                if model_type == "Random Forest":
                    n_estimators = st.slider("Number of Trees", 50, 500, 100, 10)
                    max_depth = st.slider("Max Tree Depth", 3, 20, 10)
                elif model_type == "XGBoost":
                    learning_rate = st.slider("Learning Rate", 0.01, 0.3, 0.1, 0.01)
                    n_estimators = st.slider("Number of Trees", 50, 500, 100, 10)
                    max_depth = st.slider("Max Tree Depth", 3, 20, 6)
        
        with col2:
            st.markdown("### Data Source")
            
            data_source = st.selectbox("Training Data Source", ["Current Database", "Historical Records", "Custom Dataset"])
            
            if data_source == "Custom Dataset":
                uploaded_file = st.file_uploader("Upload Training Dataset", type=["csv", "xlsx"])
            
            include_validation = st.checkbox("Use Validation Set", value=True)
            cross_validation = st.checkbox("Use Cross Validation", value=True)
            
            if cross_validation:
                cv_folds = st.slider("Number of CV Folds", 3, 10, 5)
            
            st.markdown("### Training Options")
            
            early_stopping = st.checkbox("Enable Early Stopping", value=True)
            save_checkpoints = st.checkbox("Save Model Checkpoints", value=True)
            
            train_button = st.button("Start Training", type="primary")
            
            if train_button:
                st.success("Training initiated! This would start the model training process in production.")
                
                # Progress bar
                progress_text = "Training in progress. Please wait..."
                my_bar = st.progress(0, text=progress_text)
                
                for percent_complete in range(100):
                    my_bar.progress(percent_complete + 1, text=progress_text)
                    
                st.balloons()
                st.success("Model training completed successfully!")
                
        # Model registry
        st.markdown('<h2 class="section-header">Model Registry</h2>', unsafe_allow_html=True)
        
        # Convert models to DataFrame for display
        models_df = pd.DataFrame(data['models'])
        st.dataframe(models_df[['model_id', 'name', 'type', 'status', 'accuracy', 'f1_score', 'last_trained']], 
                    use_container_width=True, 
                    hide_index=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Compare Models"):
                st.info("This would open the model comparison interface.")
                
        with col2:
            if st.button("Deploy Model"):
                st.info("This would open the model deployment interface.")
                
        with col3:
            if st.button("Export Model"):
                st.info("This would export the selected model.")
    
    with tab3:
        # Feature importance analysis
        st.markdown('<h2 class="section-header">Feature Importance Analysis</h2>', unsafe_allow_html=True)
        
        # Model selection for feature importance
        selected_model_id = st.selectbox(
            "Select Model", 
            [f"{m['name']} ({m['model_id']})" for m in data['models']]
        )
        model_id = selected_model_id.split('(')[-1].split(')')[0]
        
        # Feature importance chart
        feature_importance = data['feature_importance'][model_id]
        fig = create_feature_importance_chart(feature_importance)
        st.plotly_chart(fig, use_container_width=True)
        
        # Feature correlation matrix
        st.markdown('<h2 class="section-header">Feature Correlation</h2>', unsafe_allow_html=True)
        
        # Generate random correlation matrix for demonstration
        features = list(feature_importance.keys())
        n_features = len(features)
        
        # Generate a symmetric correlation matrix
        np.random.seed(42)
        corr_matrix = np.zeros((n_features, n_features))
        for i in range(n_features):
            for j in range(i, n_features):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    corr = np.random.uniform(-0.7, 0.7)
                    corr_matrix[i, j] = corr
                    corr_matrix[j, i] = corr
        
        # Create heatmap
        fig = px.imshow(
            corr_matrix,
            x=features,
            y=features,
            color_continuous_scale='RdBu_r',
            zmin=-1,
            zmax=1,
            labels=dict(color="Correlation")
        )
        
        fig.update_layout(
            title='Feature Correlation Matrix',
            height=500,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Feature explanation for a specific property
        st.markdown('<h2 class="section-header">Individual Property Feature Explanation</h2>', unsafe_allow_html=True)
        
        # Property selection
        property_id = st.selectbox(
            "Select Property for SHAP Analysis",
            [f"PROP_{i:04d} - {i+100} Main St, Brunswick, ME" for i in range(5)]
        )
        
        if st.button("Generate SHAP Analysis"):
            # This would generate actual SHAP values in production
            st.info("Generating SHAP values for feature explanation")
            
            # Generate fake SHAP values
            shap_values = {}
            base_value = 50
            
            for feature, importance in feature_importance.items():
                # Random value between -20 and +20, weighted by feature importance
                shap_values[feature] = round(np.random.uniform(-1, 1) * importance * 100, 2)
            
            # Sort by absolute contribution
            shap_sorted = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
            
            # Display as a waterfall chart
            feature_names = [item[0] for item in shap_sorted]
            values = [item[1] for item in shap_sorted]
            
            # Calculate cumulative values
            cumulative = base_value
            measure = ['absolute'] + ['relative'] * len(values)
            x_values = [base_value] + values
            
            # Create text labels
            text = [f"Base<br>Value<br>{base_value:.1f}"]
            for i, val in enumerate(values):
                if val >= 0:
                    text.append(f"+{val:.1f}")
                else:
                    text.append(f"{val:.1f}")
            
            # Create the waterfall chart
            fig = go.Figure(go.Waterfall(
                name="SHAP",
                orientation="v",
                measure=measure,
                x=[0] * (len(values) + 1),
                y=x_values,
                textposition="outside",
                text=text,
                connector={"line": {"color": "rgb(63, 63, 63)"}},
                decreasing={"marker": {"color": "#EF553B"}},
                increasing={"marker": {"color": "#00CC96"}},
                hoverinfo="none"
            ))
            
            fig.update_layout(
                title="SHAP Feature Impact on Lead Score",
                showlegend=False,
                xaxis=dict(
                    tickmode='array',
                    tickvals=list(range(len(x_values))),
                    ticktext=["Base Value"] + feature_names,
                    tickangle=45
                ),
                yaxis=dict(title="Lead Score Impact"),
                height=500,
                margin=dict(l=10, r=10, t=50, b=100)
            )
            
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    ml_control_panel()
