"""
Advanced text analysis capabilities for property data
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from transformers import (
    pipeline,
    AutoModelForSequenceClassification,
    AutoTokenizer
)
import spacy
from textblob import TextBlob
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from gensim.models import Word2Vec
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import json

class AdvancedTextAnalyzer:
    """
    Advanced text analysis including:
    1. Deep property description analysis
    2. Document classification
    3. Entity extraction
    4. Topic modeling
    5. Semantic search
    6. Trend detection
    7. Comparative analysis
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Initialize NLP components
        self.nlp = spacy.load('en_core_web_sm')
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Initialize models
        self._initialize_models()
        
        # Configure analysis parameters
        self.params = {
            'min_description_length': 50,
            'max_summary_length': 200,
            'similarity_threshold': 0.7,
            'min_topic_coherence': 0.6,
            'max_topics': 10
        }
        
        if 'text_params' in config:
            self.params.update(config['text_params'])

    def analyze_property_content(self, properties: List[Dict]) -> Dict:
        """
        Comprehensive analysis of property content
        """
        try:
            results = {}
            
            # Extract all text content
            content = self._extract_property_content(properties)
            
            # Analyze descriptions
            results['descriptions'] = self._analyze_descriptions(
                content['descriptions']
            )
            
            # Analyze features
            results['features'] = self._analyze_features(
                content['features']
            )
            
            # Analyze conditions
            results['conditions'] = self._analyze_conditions(
                content['conditions']
            )
            
            # Analyze locations
            results['locations'] = self._analyze_locations(
                content['locations']
            )
            
            # Find patterns
            results['patterns'] = self._find_content_patterns(content)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing property content: {str(e)}")
            return {}

    def classify_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Classify documents by type and content
        """
        try:
            classifications = []
            
            for doc in documents:
                # Get document text
                text = doc.get('content', '')
                if not text:
                    continue
                
                # Classify document type
                doc_type = self._classify_document_type(text)
                
                # Classify content
                content_classes = self._classify_document_content(text)
                
                # Extract key information
                key_info = self._extract_key_information(text, doc_type)
                
                classifications.append({
                    'document_id': doc.get('document_id'),
                    'type': doc_type,
                    'content_classes': content_classes,
                    'key_information': key_info,
                    'confidence': self._calculate_classification_confidence(
                        doc_type,
                        content_classes
                    )
                })
            
            return classifications
            
        except Exception as e:
            self.logger.error(f"Error classifying documents: {str(e)}")
            return []

    def extract_entities(self, text: str) -> Dict:
        """
        Extract and classify entities from text
        """
        try:
            entities = {
                'people': [],
                'organizations': [],
                'locations': [],
                'dates': [],
                'money': [],
                'percentages': [],
                'other': []
            }
            
            # Process with spaCy
            doc = self.nlp(text)
            
            # Extract entities
            for ent in doc.ents:
                if ent.label_ in ['PERSON']:
                    entities['people'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
                elif ent.label_ in ['ORG']:
                    entities['organizations'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
                elif ent.label_ in ['GPE', 'LOC']:
                    entities['locations'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
                elif ent.label_ in ['DATE']:
                    entities['dates'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
                elif ent.label_ in ['MONEY']:
                    entities['money'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
                elif ent.label_ in ['PERCENT']:
                    entities['percentages'].append({
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
                else:
                    entities['other'].append({
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
            
            return entities
            
        except Exception as e:
            self.logger.error(f"Error extracting entities: {str(e)}")
            return {}

    def analyze_topics(self, texts: List[str]) -> Dict:
        """
        Analyze topics in text collection
        """
        try:
            results = {}
            
            # Preprocess texts
            processed_texts = [
                self._preprocess_text(text)
                for text in texts
            ]
            
            # Extract topics
            topics = self._extract_topics(processed_texts)
            
            # Analyze topic distribution
            distribution = self._analyze_topic_distribution(
                processed_texts,
                topics
            )
            
            # Find topic trends
            trends = self._find_topic_trends(
                processed_texts,
                topics,
                distribution
            )
            
            results = {
                'topics': topics,
                'distribution': distribution,
                'trends': trends,
                'coherence': self._calculate_topic_coherence(topics)
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error analyzing topics: {str(e)}")
            return {}

    def semantic_search(self,
                       query: str,
                       documents: List[Dict],
                       top_k: int = 5) -> List[Dict]:
        """
        Perform semantic search over documents
        """
        try:
            results = []
            
            # Encode query
            query_embedding = self._encode_text(query)
            
            # Encode documents
            doc_embeddings = [
                self._encode_text(doc.get('content', ''))
                for doc in documents
            ]
            
            # Calculate similarities
            similarities = [
                cosine_similarity(
                    query_embedding.reshape(1, -1),
                    doc_emb.reshape(1, -1)
                )[0][0]
                for doc_emb in doc_embeddings
            ]
            
            # Get top results
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            for idx in top_indices:
                results.append({
                    'document': documents[idx],
                    'score': float(similarities[idx]),
                    'highlights': self._get_highlights(
                        query,
                        documents[idx].get('content', '')
                    )
                })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error performing semantic search: {str(e)}")
            return []

    def detect_trends(self, texts: List[Dict]) -> Dict:
        """
        Detect trends in text data over time
        """
        try:
            trends = {}
            
            # Sort texts by date
            sorted_texts = sorted(
                texts,
                key=lambda x: x.get('date', ''),
                reverse=True
            )
            
            # Extract temporal patterns
            trends['temporal'] = self._extract_temporal_patterns(sorted_texts)
            
            # Extract feature trends
            trends['features'] = self._extract_feature_trends(sorted_texts)
            
            # Extract price trends
            trends['prices'] = self._extract_price_trends(sorted_texts)
            
            # Extract sentiment trends
            trends['sentiment'] = self._extract_sentiment_trends(sorted_texts)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error detecting trends: {str(e)}")
            return {}

    def compare_descriptions(self,
                           desc1: str,
                           desc2: str) -> Dict:
        """
        Compare two property descriptions
        """
        try:
            comparison = {}
            
            # Calculate similarity
            comparison['similarity'] = self._calculate_text_similarity(
                desc1,
                desc2
            )
            
            # Compare features
            comparison['features'] = self._compare_features(desc1, desc2)
            
            # Compare sentiment
            comparison['sentiment'] = self._compare_sentiment(desc1, desc2)
            
            # Compare entities
            comparison['entities'] = self._compare_entities(desc1, desc2)
            
            # Compare topics
            comparison['topics'] = self._compare_topics(desc1, desc2)
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing descriptions: {str(e)}")
            return {}

    def _initialize_models(self):
        """Initialize NLP models"""
        try:
            # Initialize transformers
            self.tokenizer = AutoTokenizer.from_pretrained(
                'distilbert-base-uncased'
            )
            self.model = AutoModelForSequenceClassification.from_pretrained(
                'distilbert-base-uncased'
            )
            
            # Initialize pipelines
            self.sentiment_pipeline = pipeline(
                'sentiment-analysis',
                model='distilbert-base-uncased-finetuned-sst-2-english'
            )
            self.summarization_pipeline = pipeline(
                'summarization',
                model='facebook/bart-large-cnn'
            )
            
            # Initialize Word2Vec model
            self.word2vec = Word2Vec(
                vector_size=100,
                window=5,
                min_count=1,
                workers=4
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing models: {str(e)}")

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        try:
            # Lowercase
            text = text.lower()
            
            # Tokenize
            tokens = word_tokenize(text)
            
            # Remove stopwords and punctuation
            tokens = [
                token for token in tokens
                if token not in self.stop_words
                and token.isalnum()
            ]
            
            # Lemmatize
            tokens = [
                self.lemmatizer.lemmatize(token)
                for token in tokens
            ]
            
            return ' '.join(tokens)
            
        except Exception as e:
            self.logger.error(f"Error preprocessing text: {str(e)}")
            return text

    def _extract_property_content(self, properties: List[Dict]) -> Dict:
        """Extract text content from properties"""
        try:
            content = {
                'descriptions': [],
                'features': [],
                'conditions': [],
                'locations': []
            }
            
            for prop in properties:
                # Extract description
                if 'description' in prop:
                    content['descriptions'].append(prop['description'])
                
                # Extract features
                if 'features' in prop:
                    content['features'].extend(prop['features'])
                
                # Extract conditions
                if 'condition' in prop:
                    content['conditions'].append(prop['condition'])
                
                # Extract location
                if 'location' in prop:
                    content['locations'].append(
                        json.dumps(prop['location'])
                    )
            
            return content
            
        except Exception as e:
            self.logger.error(f"Error extracting content: {str(e)}")
            return {}
