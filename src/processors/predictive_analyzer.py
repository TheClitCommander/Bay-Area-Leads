"""
Provides predictive analytics and machine learning-based insights
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.model_selection import train_test_split
import xgboost as xgb
from prophet import Prophet

class PredictiveAnalyzer:
    """
    Provides predictive analytics including:
    1. Value prediction
    2. Market trend forecasting
    3. Investment opportunity prediction
    4. Risk prediction
    5. Anomaly detection
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Configure models
        self.models = {
            'value': None,
            'trends': None,
            'opportunity': None,
            'risk': None,
            'anomaly': None
        }
        
        # Configure feature importance tracking
        self.feature_importance = {}
        
        # Initialize scalers
        self.scalers = {}

    def train_models(self, training_data: List[Dict]) -> Dict:
        """
        Train all predictive models
        """
        try:
            results = {}
            
            # Prepare training data
            df = pd.DataFrame(training_data)
            
            # Train value prediction model
            results['value'] = self._train_value_model(df)
            
            # Train trend forecasting model
            results['trends'] = self._train_trend_model(df)
            
            # Train opportunity prediction model
            results['opportunity'] = self._train_opportunity_model(df)
            
            # Train risk prediction model
            results['risk'] = self._train_risk_model(df)
            
            # Train anomaly detection model
            results['anomaly'] = self._train_anomaly_model(df)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error training models: {str(e)}")
            return {}

    def predict_property_values(self, properties: List[Dict]) -> List[Dict]:
        """
        Predict future property values
        """
        try:
            predictions = []
            
            for prop in properties:
                try:
                    # Get features for prediction
                    features = self._extract_value_features(prop)
                    
                    # Make predictions for different timeframes
                    pred = {
                        'property_id': prop['property_id'],
                        'current_value': prop.get('assessment', {}).get('total_value'),
                        'predictions': {
                            '1_year': self._predict_value(features, 1),
                            '3_year': self._predict_value(features, 3),
                            '5_year': self._predict_value(features, 5)
                        },
                        'confidence_intervals': self._calculate_value_confidence(
                            features
                        ),
                        'factors': self._identify_value_factors(features)
                    }
                    
                    predictions.append(pred)
                    
                except Exception as e:
                    self.logger.warning(f"Error predicting value: {str(e)}")
                    continue
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting property values: {str(e)}")
            return []

    def forecast_market_trends(self, 
                             market_data: List[Dict],
                             forecast_period: int = 12) -> Dict:
        """
        Forecast market trends using Prophet
        """
        try:
            forecasts = {}
            
            # Prepare data for Prophet
            df = pd.DataFrame(market_data)
            
            # Forecast different metrics
            metrics = ['median_price', 'sales_volume', 'days_on_market']
            
            for metric in metrics:
                try:
                    # Prepare Prophet dataframe
                    prophet_df = pd.DataFrame({
                        'ds': pd.to_datetime(df['date']),
                        'y': df[metric]
                    })
                    
                    # Create and fit model
                    model = Prophet(
                        yearly_seasonality=True,
                        weekly_seasonality=True,
                        daily_seasonality=False
                    )
                    model.fit(prophet_df)
                    
                    # Make future dataframe
                    future = model.make_future_dataframe(
                        periods=forecast_period,
                        freq='M'
                    )
                    
                    # Forecast
                    forecast = model.predict(future)
                    
                    # Extract results
                    forecasts[metric] = {
                        'forecast': forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
                        .tail(forecast_period)
                        .to_dict('records'),
                        'components': model.plot_components(forecast)
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Error forecasting {metric}: {str(e)}")
                    continue
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Error forecasting market trends: {str(e)}")
            return {}

    def predict_opportunities(self, properties: List[Dict]) -> List[Dict]:
        """
        Predict investment opportunities
        """
        try:
            predictions = []
            
            for prop in properties:
                try:
                    # Extract opportunity features
                    features = self._extract_opportunity_features(prop)
                    
                    # Make predictions
                    pred = {
                        'property_id': prop['property_id'],
                        'opportunity_score': self._predict_opportunity_score(
                            features
                        ),
                        'opportunity_type': self._predict_opportunity_type(
                            features
                        ),
                        'potential_returns': self._predict_potential_returns(
                            features
                        ),
                        'confidence': self._calculate_opportunity_confidence(
                            features
                        ),
                        'key_factors': self._identify_opportunity_factors(
                            features
                        )
                    }
                    
                    predictions.append(pred)
                    
                except Exception as e:
                    self.logger.warning(f"Error predicting opportunity: {str(e)}")
                    continue
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting opportunities: {str(e)}")
            return []

    def predict_risks(self, properties: List[Dict]) -> List[Dict]:
        """
        Predict property and investment risks
        """
        try:
            predictions = []
            
            for prop in properties:
                try:
                    # Extract risk features
                    features = self._extract_risk_features(prop)
                    
                    # Make predictions
                    pred = {
                        'property_id': prop['property_id'],
                        'risk_score': self._predict_risk_score(features),
                        'risk_factors': self._predict_risk_factors(features),
                        'risk_trends': self._predict_risk_trends(features),
                        'mitigation_strategies': self._suggest_risk_mitigation(
                            features
                        )
                    }
                    
                    predictions.append(pred)
                    
                except Exception as e:
                    self.logger.warning(f"Error predicting risks: {str(e)}")
                    continue
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting risks: {str(e)}")
            return []

    def detect_anomalies(self, properties: List[Dict]) -> List[Dict]:
        """
        Detect anomalies in property data
        """
        try:
            results = []
            
            # Convert to dataframe
            df = pd.DataFrame(properties)
            
            # Extract features for anomaly detection
            features = self._extract_anomaly_features(df)
            
            # Detect anomalies
            anomalies = self._detect_property_anomalies(features)
            
            # Analyze anomalies
            for i, prop in df.iterrows():
                try:
                    if anomalies[i] == -1:  # Anomaly detected
                        analysis = {
                            'property_id': prop['property_id'],
                            'anomaly_type': self._classify_anomaly(
                                features.iloc[i]
                            ),
                            'anomaly_score': self._calculate_anomaly_score(
                                features.iloc[i]
                            ),
                            'contributing_factors': self._identify_anomaly_factors(
                                features.iloc[i]
                            ),
                            'recommendations': self._generate_anomaly_recommendations(
                                features.iloc[i]
                            )
                        }
                        
                        results.append(analysis)
                        
                except Exception as e:
                    self.logger.warning(f"Error analyzing anomaly: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")
            return []

    def _train_value_model(self, df: pd.DataFrame) -> Dict:
        """Train value prediction model"""
        try:
            # Extract features and target
            features = self._extract_value_features_batch(df)
            target = df['assessment'].apply(
                lambda x: x.get('total_value')
            ).fillna(0)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features, target, test_size=0.2
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = xgb.XGBRegressor(
                objective='reg:squarederror',
                n_estimators=100
            )
            model.fit(X_train_scaled, y_train)
            
            # Save model and scaler
            self.models['value'] = model
            self.scalers['value'] = scaler
            
            # Calculate feature importance
            self.feature_importance['value'] = dict(
                zip(features.columns, model.feature_importances_)
            )
            
            # Evaluate model
            train_score = model.score(X_train_scaled, y_train)
            test_score = model.score(X_test_scaled, y_test)
            
            return {
                'train_score': float(train_score),
                'test_score': float(test_score),
                'feature_importance': self.feature_importance['value']
            }
            
        except Exception as e:
            self.logger.error(f"Error training value model: {str(e)}")
            return {}

    def _train_trend_model(self, df: pd.DataFrame) -> Dict:
        """Train market trend forecasting model"""
        try:
            results = {}
            
            # Train models for different metrics
            metrics = ['median_price', 'sales_volume', 'days_on_market']
            
            for metric in metrics:
                try:
                    # Prepare Prophet dataframe
                    prophet_df = pd.DataFrame({
                        'ds': pd.to_datetime(df['date']),
                        'y': df[metric]
                    })
                    
                    # Create and fit model
                    model = Prophet(
                        yearly_seasonality=True,
                        weekly_seasonality=True,
                        daily_seasonality=False,
                        changepoint_prior_scale=0.05
                    )
                    
                    # Add additional regressors
                    if 'market_conditions' in df.columns:
                        model.add_regressor('market_conditions')
                    
                    model.fit(prophet_df)
                    
                    # Save model
                    self.models[f'trend_{metric}'] = model
                    
                    # Evaluate model
                    cv_results = cross_validation(
                        model,
                        initial='730 days',
                        period='180 days',
                        horizon='365 days'
                    )
                    
                    performance = performance_metrics(cv_results)
                    
                    results[metric] = {
                        'rmse': float(performance['rmse'].mean()),
                        'mape': float(performance['mape'].mean())
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Error training {metric} model: {str(e)}")
                    continue
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error training trend model: {str(e)}")
            return {}

    def _train_opportunity_model(self, df: pd.DataFrame) -> Dict:
        """Train opportunity prediction model"""
        try:
            # Extract features
            features = self._extract_opportunity_features_batch(df)
            
            # Create target variables
            targets = {
                'opportunity_score': df['opportunity_score'],
                'opportunity_type': df['opportunity_type']
            }
            
            results = {}
            
            # Train regression model for opportunity score
            score_model = RandomForestRegressor(n_estimators=100)
            score_model.fit(features, targets['opportunity_score'])
            
            self.models['opportunity_score'] = score_model
            
            # Train classification model for opportunity type
            type_model = RandomForestClassifier(n_estimators=100)
            type_model.fit(features, targets['opportunity_type'])
            
            self.models['opportunity_type'] = type_model
            
            # Calculate feature importance
            self.feature_importance['opportunity'] = {
                'score': dict(
                    zip(features.columns, score_model.feature_importances_)
                ),
                'type': dict(
                    zip(features.columns, type_model.feature_importances_)
                )
            }
            
            # Evaluate models
            results['score_model'] = {
                'r2_score': float(
                    score_model.score(features, targets['opportunity_score'])
                )
            }
            
            results['type_model'] = {
                'accuracy': float(
                    type_model.score(features, targets['opportunity_type'])
                )
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error training opportunity model: {str(e)}")
            return {}

    def _train_risk_model(self, df: pd.DataFrame) -> Dict:
        """Train risk prediction model"""
        try:
            # Extract features
            features = self._extract_risk_features_batch(df)
            
            # Create target variables
            targets = {
                'risk_score': df['risk_score'],
                'risk_factors': df['risk_factors'].apply(
                    lambda x: [factor['type'] for factor in x]
                )
            }
            
            results = {}
            
            # Train regression model for risk score
            score_model = RandomForestRegressor(n_estimators=100)
            score_model.fit(features, targets['risk_score'])
            
            self.models['risk_score'] = score_model
            
            # Train multi-label classification for risk factors
            mlb = MultiLabelBinarizer()
            risk_factors_binary = mlb.fit_transform(targets['risk_factors'])
            
            factor_model = MultiOutputClassifier(
                RandomForestClassifier(n_estimators=100)
            )
            factor_model.fit(features, risk_factors_binary)
            
            self.models['risk_factors'] = factor_model
            self.models['risk_factor_labels'] = mlb
            
            # Calculate feature importance
            self.feature_importance['risk'] = dict(
                zip(features.columns, score_model.feature_importances_)
            )
            
            # Evaluate models
            results['score_model'] = {
                'r2_score': float(
                    score_model.score(features, targets['risk_score'])
                )
            }
            
            results['factor_model'] = {
                'accuracy': float(
                    np.mean([
                        estimator.score(features, risk_factors_binary[:, i])
                        for i, estimator in enumerate(factor_model.estimators_)
                    ])
                )
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error training risk model: {str(e)}")
            return {}

    def _train_anomaly_model(self, df: pd.DataFrame) -> Dict:
        """Train anomaly detection model"""
        try:
            # Extract features
            features = self._extract_anomaly_features(df)
            
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Train isolation forest
            model = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            model.fit(features_scaled)
            
            # Save model and scaler
            self.models['anomaly'] = model
            self.scalers['anomaly'] = scaler
            
            # Calculate feature importance using random forest
            rf_model = RandomForestClassifier(n_estimators=100)
            
            # Create synthetic labels (normal vs anomaly)
            labels = model.predict(features_scaled)
            rf_model.fit(features_scaled, labels)
            
            self.feature_importance['anomaly'] = dict(
                zip(features.columns, rf_model.feature_importances_)
            )
            
            return {
                'n_samples_train': len(features),
                'n_features': features.shape[1],
                'feature_importance': self.feature_importance['anomaly']
            }
            
        except Exception as e:
            self.logger.error(f"Error training anomaly model: {str(e)}")
            return {}
