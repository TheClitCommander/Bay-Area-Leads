"""
Main processor that integrates all components for lead processing
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from .data_cleaner import DataCleaner
from .data_standardizer import DataStandardizer
from .data_merger import DataMerger
from .data_enricher import DataEnricher
from .relationship_analyzer import RelationshipAnalyzer
from .investment_analyzer import InvestmentAnalyzer
from .opportunity_detector import OpportunityDetector
from .predictive_analyzer import PredictiveAnalyzer
from .visualization_generator import VisualizationGenerator
from .network_analyzer import NetworkAnalyzer
from .text_analyzer import TextAnalyzer

class LeadProcessor:
    """
    Main processor that:
    1. Coordinates all processing components
    2. Manages data flow between components
    3. Handles parallel processing
    4. Provides unified interface
    5. Generates final outputs
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Initialize components
        self.cleaner = DataCleaner(config.get('cleaner_config'))
        self.standardizer = DataStandardizer(config.get('standardizer_config'))
        self.merger = DataMerger(config.get('merger_config'))
        self.enricher = DataEnricher(config.get('enricher_config'))
        self.relationship_analyzer = RelationshipAnalyzer(config.get('relationship_config'))
        self.investment_analyzer = InvestmentAnalyzer(config.get('investment_config'))
        self.opportunity_detector = OpportunityDetector(config.get('opportunity_config'))
        self.predictive_analyzer = PredictiveAnalyzer(config.get('predictive_config'))
        self.visualization_generator = VisualizationGenerator(config.get('visualization_config'))
        self.network_analyzer = NetworkAnalyzer(config.get('network_config'))
        self.text_analyzer = TextAnalyzer(config.get('text_config'))
        
        # Configure processing
        self.max_workers = config.get('max_workers', 4)
        self.batch_size = config.get('batch_size', 100)
        
        # Initialize storage
        self.processed_data = {}
        self.analysis_results = {}
        self.predictions = {}
        self.visualizations = {}

    def process_leads(self, raw_data: List[Dict]) -> Dict:
        """
        Process raw lead data through all components
        """
        try:
            results = {}
            
            # Step 1: Clean and standardize data
            cleaned_data = self._clean_and_standardize(raw_data)
            
            # Step 2: Merge and enrich data
            enriched_data = self._merge_and_enrich(cleaned_data)
            
            # Step 3: Perform analysis
            analysis_results = self._analyze_data(enriched_data)
            
            # Step 4: Generate predictions
            predictions = self._generate_predictions(enriched_data, analysis_results)
            
            # Step 5: Create visualizations
            visualizations = self._create_visualizations(
                enriched_data,
                analysis_results,
                predictions
            )
            
            # Step 6: Generate final results
            results = self._generate_final_results(
                enriched_data,
                analysis_results,
                predictions,
                visualizations
            )
            
            # Store results
            self.processed_data = enriched_data
            self.analysis_results = analysis_results
            self.predictions = predictions
            self.visualizations = visualizations
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing leads: {str(e)}")
            return {}

    def update_leads(self, new_data: List[Dict]) -> Dict:
        """
        Update existing processed leads with new data
        """
        try:
            # Process new data
            new_results = self.process_leads(new_data)
            
            # Merge with existing data
            merged_results = self._merge_results(
                self.processed_data,
                new_results
            )
            
            # Update storage
            self.processed_data.update(merged_results['processed_data'])
            self.analysis_results.update(merged_results['analysis_results'])
            self.predictions.update(merged_results['predictions'])
            self.visualizations.update(merged_results['visualizations'])
            
            return merged_results
            
        except Exception as e:
            self.logger.error(f"Error updating leads: {str(e)}")
            return {}

    def get_top_opportunities(self, 
                            filters: Dict = None,
                            limit: int = 10) -> List[Dict]:
        """
        Get top investment opportunities
        """
        try:
            opportunities = []
            
            # Get all opportunities
            all_opportunities = self.opportunity_detector.detect_opportunities(
                self.processed_data
            )
            
            # Apply filters
            if filters:
                filtered = self._apply_filters(all_opportunities, filters)
            else:
                filtered = all_opportunities
            
            # Sort by score
            sorted_opportunities = sorted(
                filtered,
                key=lambda x: x['total_score'],
                reverse=True
            )
            
            # Get top opportunities
            top = sorted_opportunities[:limit]
            
            # Enhance with additional data
            for opp in top:
                property_data = self.processed_data[opp['property_id']]
                
                opportunities.append({
                    **opp,
                    'property_data': property_data,
                    'analysis': self.analysis_results.get(opp['property_id']),
                    'predictions': self.predictions.get(opp['property_id']),
                    'visualizations': self.visualizations.get(opp['property_id'])
                })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error getting top opportunities: {str(e)}")
            return []

    def analyze_market(self, market_data: Dict) -> Dict:
        """
        Analyze market conditions and trends
        """
        try:
            analysis = {}
            
            # Analyze current conditions
            analysis['current_conditions'] = self._analyze_current_conditions(
                market_data
            )
            
            # Analyze trends
            analysis['trends'] = self._analyze_market_trends(market_data)
            
            # Generate forecasts
            analysis['forecasts'] = self._generate_market_forecasts(market_data)
            
            # Analyze opportunities
            analysis['opportunities'] = self._analyze_market_opportunities(
                market_data
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing market: {str(e)}")
            return {}

    def generate_reports(self, 
                        property_ids: List[str] = None,
                        report_type: str = 'full') -> Dict:
        """
        Generate analysis reports
        """
        try:
            reports = {}
            
            # Get properties to report on
            if property_ids:
                properties = [
                    self.processed_data[pid]
                    for pid in property_ids
                    if pid in self.processed_data
                ]
            else:
                properties = list(self.processed_data.values())
            
            # Generate reports in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_property = {
                    executor.submit(
                        self._generate_property_report,
                        prop,
                        report_type
                    ): prop['property_id']
                    for prop in properties
                }
                
                for future in as_completed(future_to_property):
                    property_id = future_to_property[future]
                    try:
                        reports[property_id] = future.result()
                    except Exception as e:
                        self.logger.error(
                            f"Error generating report for {property_id}: {str(e)}"
                        )
            
            return reports
            
        except Exception as e:
            self.logger.error(f"Error generating reports: {str(e)}")
            return {}

    def _clean_and_standardize(self, raw_data: List[Dict]) -> List[Dict]:
        """Clean and standardize raw data"""
        try:
            # Process in batches
            cleaned = []
            for i in range(0, len(raw_data), self.batch_size):
                batch = raw_data[i:i + self.batch_size]
                
                # Clean batch
                cleaned_batch = self.cleaner.clean_data(batch)
                
                # Standardize batch
                standardized_batch = self.standardizer.standardize_data(
                    cleaned_batch
                )
                
                cleaned.extend(standardized_batch)
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning and standardizing: {str(e)}")
            return []

    def _merge_and_enrich(self, cleaned_data: List[Dict]) -> List[Dict]:
        """Merge and enrich cleaned data"""
        try:
            # Merge data
            merged = self.merger.merge_data(cleaned_data)
            
            # Enrich in parallel
            enriched = []
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_property = {
                    executor.submit(
                        self.enricher.enrich_property,
                        prop
                    ): prop['property_id']
                    for prop in merged
                }
                
                for future in as_completed(future_to_property):
                    try:
                        enriched.append(future.result())
                    except Exception as e:
                        self.logger.error(f"Error enriching property: {str(e)}")
            
            return enriched
            
        except Exception as e:
            self.logger.error(f"Error merging and enriching: {str(e)}")
            return []

    def _analyze_data(self, enriched_data: List[Dict]) -> Dict:
        """Perform comprehensive analysis"""
        try:
            analysis = {}
            
            # Analyze relationships
            analysis['relationships'] = self.relationship_analyzer.analyze_relationships(
                enriched_data
            )
            
            # Analyze investments
            analysis['investments'] = self.investment_analyzer.analyze_investments(
                enriched_data
            )
            
            # Detect opportunities
            analysis['opportunities'] = self.opportunity_detector.detect_opportunities(
                enriched_data
            )
            
            # Analyze networks
            analysis['networks'] = self.network_analyzer.analyze_networks(
                enriched_data
            )
            
            # Analyze text data
            analysis['text'] = self.text_analyzer.analyze_text(
                enriched_data
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing data: {str(e)}")
            return {}

    def _generate_predictions(self,
                            enriched_data: List[Dict],
                            analysis_results: Dict) -> Dict:
        """Generate predictions"""
        try:
            predictions = {}
            
            # Train models if needed
            self.predictive_analyzer.train_models(enriched_data)
            
            # Generate predictions
            predictions['values'] = self.predictive_analyzer.predict_property_values(
                enriched_data
            )
            
            predictions['trends'] = self.predictive_analyzer.forecast_market_trends(
                enriched_data
            )
            
            predictions['opportunities'] = self.predictive_analyzer.predict_opportunities(
                enriched_data
            )
            
            predictions['risks'] = self.predictive_analyzer.predict_risks(
                enriched_data
            )
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error generating predictions: {str(e)}")
            return {}

    def _create_visualizations(self,
                             enriched_data: List[Dict],
                             analysis_results: Dict,
                             predictions: Dict) -> Dict:
        """Create visualizations"""
        try:
            visualizations = {}
            
            # Create property map
            visualizations['map'] = self.visualization_generator.create_property_map(
                enriched_data
            )
            
            # Create market visualizations
            visualizations['market'] = self.visualization_generator.create_market_visualizations(
                analysis_results['market']
            )
            
            # Create investment visualizations
            visualizations['investment'] = self.visualization_generator.create_investment_visualizations(
                analysis_results['investments'],
                enriched_data
            )
            
            # Create network visualizations
            visualizations['network'] = self.visualization_generator.create_network_visualizations(
                analysis_results['networks']
            )
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {str(e)}")
            return {}

    def _generate_final_results(self,
                              enriched_data: List[Dict],
                              analysis_results: Dict,
                              predictions: Dict,
                              visualizations: Dict) -> Dict:
        """Generate final processed results"""
        try:
            results = {
                'processed_data': enriched_data,
                'analysis_results': analysis_results,
                'predictions': predictions,
                'visualizations': visualizations,
                'summary': self._generate_summary(
                    enriched_data,
                    analysis_results,
                    predictions
                ),
                'recommendations': self._generate_recommendations(
                    enriched_data,
                    analysis_results,
                    predictions
                ),
                'metadata': {
                    'processed_at': datetime.now().isoformat(),
                    'property_count': len(enriched_data),
                    'version': '1.0'
                }
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating final results: {str(e)}")
            return {}
