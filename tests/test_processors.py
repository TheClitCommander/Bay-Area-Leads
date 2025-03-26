"""
Tests for data processors
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import os
from datetime import datetime

from src.processors.cleaner import DataCleaner
from src.processors.standardizer import DataStandardizer
from src.processors.merger import DataMerger
from src.processors.enricher import DataEnricher
from src.processors.text_analyzer import TextAnalyzer
from src.processors.network_analyzer import NetworkAnalyzer

class TestDataCleaner(unittest.TestCase):
    def setUp(self):
        self.cleaner = DataCleaner()
        self.test_data = [
            {
                'property_id': 'P123',
                'address': '123 Main St',
                'value': '300,000',
                'date': '01/15/2025'
            },
            {
                'property_id': 'P123',  # Duplicate
                'address': None,        # Missing
                'value': 'invalid',     # Invalid
                'date': '2025-01-15'    # Different format
            }
        ]

    def test_remove_duplicates(self):
        result = self.cleaner.clean_data(self.test_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['property_id'], 'P123')

    def test_handle_missing_values(self):
        result = self.cleaner.clean_data(self.test_data)
        self.assertIsNotNone(result[0]['address'])

    def test_standardize_values(self):
        result = self.cleaner.clean_data(self.test_data)
        self.assertTrue(isinstance(result[0]['value'], float))
        self.assertEqual(result[0]['value'], 300000.0)

    def test_validate_data(self):
        invalid_data = [{'invalid': 'data'}]
        result = self.cleaner.clean_data(invalid_data)
        self.assertEqual(len(result), 0)

class TestDataStandardizer(unittest.TestCase):
    def setUp(self):
        self.standardizer = DataStandardizer()
        self.test_data = [
            {
                'address': '123 MAIN ST',
                'phone': '(555) 123-4567',
                'date': '01/15/2025',
                'price': '$300,000'
            }
        ]

    def test_standardize_address(self):
        result = self.standardizer.standardize_data(self.test_data)
        self.assertEqual(
            result[0]['address'],
            '123 Main Street'
        )

    def test_standardize_phone(self):
        result = self.standardizer.standardize_data(self.test_data)
        self.assertEqual(
            result[0]['phone'],
            '5551234567'
        )

    def test_standardize_date(self):
        result = self.standardizer.standardize_data(self.test_data)
        self.assertEqual(
            result[0]['date'],
            '2025-01-15'
        )

    def test_standardize_price(self):
        result = self.standardizer.standardize_data(self.test_data)
        self.assertEqual(
            result[0]['price'],
            300000.0
        )

class TestDataMerger(unittest.TestCase):
    def setUp(self):
        self.merger = DataMerger()
        self.property_data = [
            {
                'property_id': 'P123',
                'address': '123 Main St'
            }
        ]
        self.tax_data = [
            {
                'parcel_id': 'T456',
                'address': '123 Main St',
                'value': 300000
            }
        ]

    def test_merge_by_address(self):
        result = self.merger.merge_data(
            self.property_data,
            self.tax_data
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['property_id'], 'P123')
        self.assertEqual(result[0]['parcel_id'], 'T456')

    def test_handle_no_match(self):
        self.tax_data[0]['address'] = '456 Other St'
        result = self.merger.merge_data(
            self.property_data,
            self.tax_data
        )
        self.assertEqual(len(result), 2)

    def test_merge_confidence(self):
        result = self.merger.merge_data(
            self.property_data,
            self.tax_data
        )
        self.assertTrue('merge_confidence' in result[0])
        self.assertGreaterEqual(result[0]['merge_confidence'], 0.0)
        self.assertLessEqual(result[0]['merge_confidence'], 1.0)

class TestDataEnricher(unittest.TestCase):
    def setUp(self):
        self.enricher = DataEnricher()
        self.test_data = [
            {
                'property_id': 'P123',
                'address': '123 Main St',
                'value': 300000,
                'sqft': 2000
            }
        ]

    def test_add_derived_metrics(self):
        result = self.enricher.enrich_property(self.test_data[0])
        self.assertTrue('price_per_sqft' in result)
        self.assertEqual(result['price_per_sqft'], 150.0)

    def test_add_market_context(self):
        result = self.enricher.enrich_property(self.test_data[0])
        self.assertTrue('market_context' in result)
        self.assertTrue('median_value' in result['market_context'])

    def test_add_geographic_context(self):
        result = self.enricher.enrich_property(self.test_data[0])
        self.assertTrue('geographic_context' in result)
        self.assertTrue('nearby_properties' in result['geographic_context'])

    def test_handle_missing_data(self):
        test_data = {'property_id': 'P123'}  # Missing required fields
        result = self.enricher.enrich_property(test_data)
        self.assertEqual(result, test_data)

class TestTextAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = TextAnalyzer()
        self.test_description = """
        Beautiful 3-bedroom, 2-bath home with recent renovations.
        Hardwood floors throughout, new kitchen appliances, and
        a spacious backyard. Close to schools and shopping.
        Listed at $450,000.
        """

    def test_extract_features(self):
        result = self.analyzer.analyze_property_descriptions(
            [{'description': self.test_description}]
        )
        self.assertTrue('features' in result)
        self.assertIn('hardwood floors', result['features'])
        self.assertIn('new kitchen', result['features'])

    def test_analyze_sentiment(self):
        result = self.analyzer.analyze_property_descriptions(
            [{'description': self.test_description}]
        )
        self.assertTrue('sentiment' in result)
        self.assertTrue('score' in result['sentiment'])
        self.assertTrue('label' in result['sentiment'])

    def test_extract_entities(self):
        result = self.analyzer.extract_entities(self.test_description)
        self.assertTrue('prices' in result)
        self.assertTrue('features' in result)
        self.assertTrue('locations' in result)

    def test_handle_empty_text(self):
        result = self.analyzer.analyze_property_descriptions(
            [{'description': ''}]
        )
        self.assertEqual(result['features'], [])

class TestNetworkAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = NetworkAnalyzer()
        self.test_data = [
            {
                'property_id': 'P1',
                'owner': 'John Doe',
                'transactions': [
                    {
                        'date': '2025-01-15',
                        'buyer': 'John Doe',
                        'seller': 'Jane Smith',
                        'price': 300000
                    }
                ]
            },
            {
                'property_id': 'P2',
                'owner': 'Jane Smith',
                'transactions': [
                    {
                        'date': '2025-01-16',
                        'buyer': 'John Doe',
                        'seller': 'Jane Smith',
                        'price': 400000
                    }
                ]
            }
        ]

    def test_analyze_owner_networks(self):
        result = self.analyzer.analyze_owner_networks(self.test_data)
        self.assertTrue('network_stats' in result)
        self.assertTrue('communities' in result)
        self.assertTrue('key_players' in result)

    def test_detect_patterns(self):
        result = self.analyzer.analyze_transaction_patterns(self.test_data)
        self.assertTrue('patterns' in result)
        self.assertTrue('transaction_chains' in result)
        self.assertTrue('price_patterns' in result)

    def test_identify_communities(self):
        result = self.analyzer.detect_investment_groups(self.test_data)
        self.assertTrue(len(result) > 0)
        self.assertTrue('members' in result[0])
        self.assertTrue('metrics' in result[0])

    def test_handle_empty_data(self):
        result = self.analyzer.analyze_owner_networks([])
        self.assertEqual(result['network_stats']['node_count'], 0)
        self.assertEqual(result['network_stats']['edge_count'], 0)

if __name__ == '__main__':
    unittest.main()
