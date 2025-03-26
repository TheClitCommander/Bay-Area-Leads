"""
Analyzes text data from property descriptions, permits, and documents
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from transformers import pipeline
import spacy
from textblob import TextBlob
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TextAnalyzer:
    """
    Analyzes text data including:
    1. Property descriptions
    2. Permit descriptions
    3. Market reports
    4. Owner communications
    5. Legal documents
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Load NLP models
        self.nlp = spacy.load('en_core_web_sm')
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = pipeline(
            'sentiment-analysis',
            model='distilbert-base-uncased-finetuned-sst-2-english'
        )
        
        # Initialize text vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english'
        )
        
        # Configure analysis parameters
        self.params = {
            'min_description_length': 50,
            'max_summary_length': 200,
            'similarity_threshold': 0.7
        }

    def analyze_property_descriptions(self, properties: List[Dict]) -> Dict:
        """
        Analyze property descriptions for insights
        """
        try:
            results = {}
            
            # Extract descriptions
            descriptions = [
                prop.get('description', '')
                for prop in properties
                if len(prop.get('description', '')) > self.params['min_description_length']
            ]
            
            if not descriptions:
                return results
            
            # Vectorize descriptions
            vectors = self.vectorizer.fit_transform(descriptions)
            
            # Extract key features
            features = self._extract_property_features(descriptions)
            
            # Analyze sentiment
            sentiments = self._analyze_description_sentiment(descriptions)
            
            # Find similar properties
            similarities = self._find_similar_descriptions(vectors)
            
            # Extract condition indicators
            conditions = self._extract_condition_indicators(descriptions)
            
            results = {
                'features': features,
                'sentiments': sentiments,
                'similarities': similarities,
                'conditions': conditions,
                'summaries': self._generate_summaries(descriptions)
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing descriptions: {str(e)}")
            return {}

    def analyze_permit_documents(self, permits: List[Dict]) -> Dict:
        """
        Analyze permit documents and descriptions
        """
        try:
            results = {}
            
            # Extract permit text
            permit_texts = [
                {
                    'permit_id': permit['permit_id'],
                    'description': permit.get('description', ''),
                    'comments': permit.get('comments', ''),
                    'status': permit.get('status', '')
                }
                for permit in permits
            ]
            
            if not permit_texts:
                return results
            
            # Extract work types
            work_types = self._extract_work_types(permit_texts)
            
            # Analyze complexity
            complexity = self._analyze_work_complexity(permit_texts)
            
            # Extract requirements
            requirements = self._extract_requirements(permit_texts)
            
            # Analyze status language
            status_analysis = self._analyze_status_language(permit_texts)
            
            results = {
                'work_types': work_types,
                'complexity': complexity,
                'requirements': requirements,
                'status_analysis': status_analysis,
                'summaries': self._summarize_permits(permit_texts)
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing permits: {str(e)}")
            return {}

    def analyze_market_reports(self, reports: List[Dict]) -> Dict:
        """
        Analyze market report content
        """
        try:
            results = {}
            
            # Extract report text
            report_texts = [
                {
                    'report_id': report['report_id'],
                    'content': report.get('content', ''),
                    'date': report.get('date'),
                    'source': report.get('source')
                }
                for report in reports
            ]
            
            if not report_texts:
                return results
            
            # Extract market indicators
            indicators = self._extract_market_indicators(report_texts)
            
            # Analyze sentiment
            sentiment = self._analyze_market_sentiment(report_texts)
            
            # Extract trends
            trends = self._extract_market_trends(report_texts)
            
            # Extract predictions
            predictions = self._extract_market_predictions(report_texts)
            
            results = {
                'indicators': indicators,
                'sentiment': sentiment,
                'trends': trends,
                'predictions': predictions,
                'summaries': self._summarize_reports(report_texts)
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing reports: {str(e)}")
            return {}

    def analyze_legal_documents(self, documents: List[Dict]) -> Dict:
        """
        Analyze legal documents
        """
        try:
            results = {}
            
            # Extract document text
            doc_texts = [
                {
                    'document_id': doc['document_id'],
                    'content': doc.get('content', ''),
                    'type': doc.get('type'),
                    'date': doc.get('date')
                }
                for doc in documents
            ]
            
            if not doc_texts:
                return results
            
            # Extract key terms
            terms = self._extract_legal_terms(doc_texts)
            
            # Analyze obligations
            obligations = self._analyze_legal_obligations(doc_texts)
            
            # Extract restrictions
            restrictions = self._extract_legal_restrictions(doc_texts)
            
            # Analyze risk language
            risks = self._analyze_risk_language(doc_texts)
            
            results = {
                'terms': terms,
                'obligations': obligations,
                'restrictions': restrictions,
                'risks': risks,
                'summaries': self._summarize_legal_docs(doc_texts)
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing legal documents: {str(e)}")
            return {}

    def _extract_property_features(self, descriptions: List[str]) -> Dict:
        """Extract property features from descriptions"""
        try:
            features = {
                'amenities': set(),
                'improvements': set(),
                'conditions': set(),
                'locations': set()
            }
            
            for desc in descriptions:
                doc = self.nlp(desc)
                
                # Extract noun phrases
                for chunk in doc.noun_chunks:
                    # Classify features
                    if self._is_amenity(chunk.text):
                        features['amenities'].add(chunk.text.lower())
                    elif self._is_improvement(chunk.text):
                        features['improvements'].add(chunk.text.lower())
                    elif self._is_condition(chunk.text):
                        features['conditions'].add(chunk.text.lower())
                    elif self._is_location(chunk.text):
                        features['locations'].add(chunk.text.lower())
            
            # Convert sets to sorted lists
            return {
                k: sorted(list(v))
                for k, v in features.items()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting features: {str(e)}")
            return {}

    def _analyze_description_sentiment(self, descriptions: List[str]) -> List[Dict]:
        """Analyze sentiment in property descriptions"""
        try:
            results = []
            
            for desc in descriptions:
                # Get overall sentiment
                sentiment = TextBlob(desc).sentiment
                
                # Get aspect-based sentiment
                aspects = self._extract_aspect_sentiment(desc)
                
                results.append({
                    'overall': {
                        'polarity': float(sentiment.polarity),
                        'subjectivity': float(sentiment.subjectivity)
                    },
                    'aspects': aspects
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
            return []

    def _find_similar_descriptions(self, vectors) -> List[Dict]:
        """Find similar property descriptions"""
        try:
            similarities = []
            
            # Calculate similarity matrix
            sim_matrix = cosine_similarity(vectors)
            
            # Find similar pairs
            for i in range(len(sim_matrix)):
                for j in range(i + 1, len(sim_matrix)):
                    if sim_matrix[i][j] > self.params['similarity_threshold']:
                        similarities.append({
                            'pair': (i, j),
                            'score': float(sim_matrix[i][j])
                        })
            
            return sorted(
                similarities,
                key=lambda x: x['score'],
                reverse=True
            )
            
        except Exception as e:
            self.logger.error(f"Error finding similarities: {str(e)}")
            return []

    def _extract_work_types(self, permit_texts: List[Dict]) -> Dict:
        """Extract and classify work types from permits"""
        try:
            work_types = {
                'renovation': set(),
                'addition': set(),
                'repair': set(),
                'installation': set(),
                'other': set()
            }
            
            for permit in permit_texts:
                desc = permit['description'].lower()
                
                # Classify work type
                if any(word in desc for word in ['renovate', 'remodel', 'upgrade']):
                    work_types['renovation'].add(permit['permit_id'])
                elif any(word in desc for word in ['add', 'expand', 'extend']):
                    work_types['addition'].add(permit['permit_id'])
                elif any(word in desc for word in ['repair', 'fix', 'replace']):
                    work_types['repair'].add(permit['permit_id'])
                elif any(word in desc for word in ['install', 'new']):
                    work_types['installation'].add(permit['permit_id'])
                else:
                    work_types['other'].add(permit['permit_id'])
            
            return {
                k: sorted(list(v))
                for k, v in work_types.items()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting work types: {str(e)}")
            return {}

    def _analyze_work_complexity(self, permit_texts: List[Dict]) -> List[Dict]:
        """Analyze complexity of permitted work"""
        try:
            results = []
            
            for permit in permit_texts:
                # Analyze description complexity
                complexity_indicators = {
                    'multiple_trades': self._involves_multiple_trades(permit),
                    'specialized_work': self._requires_specialized_work(permit),
                    'structural_changes': self._involves_structural_changes(permit),
                    'time_intensive': self._is_time_intensive(permit)
                }
                
                # Calculate overall complexity score
                score = sum(
                    1 for indicator in complexity_indicators.values()
                    if indicator
                ) / len(complexity_indicators)
                
                results.append({
                    'permit_id': permit['permit_id'],
                    'complexity_score': float(score),
                    'indicators': complexity_indicators
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing complexity: {str(e)}")
            return []

    def _extract_market_indicators(self, report_texts: List[Dict]) -> Dict:
        """Extract market indicators from reports"""
        try:
            indicators = {
                'price_trends': [],
                'inventory_levels': [],
                'market_conditions': [],
                'future_outlook': []
            }
            
            for report in report_texts:
                content = report['content'].lower()
                
                # Extract price trends
                price_matches = re.findall(
                    r'prices? (increased|decreased|remained stable) by (\d+(?:\.\d+)?%?)',
                    content
                )
                for direction, amount in price_matches:
                    indicators['price_trends'].append({
                        'direction': direction,
                        'amount': amount,
                        'date': report['date']
                    })
                
                # Extract inventory levels
                inventory_matches = re.findall(
                    r'inventory (up|down|stable) (\d+(?:\.\d+)?%?)',
                    content
                )
                for direction, amount in inventory_matches:
                    indicators['inventory_levels'].append({
                        'direction': direction,
                        'amount': amount,
                        'date': report['date']
                    })
                
                # Extract market conditions
                conditions = self._extract_market_conditions(content)
                indicators['market_conditions'].extend([
                    {
                        'condition': cond,
                        'date': report['date']
                    }
                    for cond in conditions
                ])
                
                # Extract future outlook
                outlook = self._extract_future_outlook(content)
                if outlook:
                    indicators['future_outlook'].append({
                        'outlook': outlook,
                        'date': report['date']
                    })
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error extracting market indicators: {str(e)}")
            return {}

    def _analyze_market_sentiment(self, report_texts: List[Dict]) -> List[Dict]:
        """Analyze sentiment in market reports"""
        try:
            results = []
            
            for report in report_texts:
                # Analyze overall sentiment
                sentiment = self.sentiment_analyzer(report['content'])[0]
                
                # Analyze aspect-specific sentiment
                aspects = {
                    'price_sentiment': self._analyze_price_sentiment(
                        report['content']
                    ),
                    'demand_sentiment': self._analyze_demand_sentiment(
                        report['content']
                    ),
                    'supply_sentiment': self._analyze_supply_sentiment(
                        report['content']
                    ),
                    'outlook_sentiment': self._analyze_outlook_sentiment(
                        report['content']
                    )
                }
                
                results.append({
                    'report_id': report['report_id'],
                    'date': report['date'],
                    'overall_sentiment': {
                        'label': sentiment['label'],
                        'score': float(sentiment['score'])
                    },
                    'aspect_sentiment': aspects
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing market sentiment: {str(e)}")
            return []
