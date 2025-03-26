"""
Tests for data collectors
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import os
from datetime import datetime

from src.collectors.permit_collector import PermitCollector
from src.collectors.tax_collector import TaxCollector
from src.collectors.utility_collector import UtilityCollector

class TestPermitCollector(unittest.TestCase):
    def setUp(self):
        self.collector = PermitCollector()
        self.mock_response = {
            'permits': [
                {
                    'permit_id': 'P123',
                    'type': 'building',
                    'status': 'approved',
                    'issue_date': '2025-01-15',
                    'description': 'New roof installation'
                }
            ]
        }

    @patch('requests.get')
    def test_collect_permits(self, mock_get):
        # Mock successful API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_response

        result = self.collector.collect('test_town')
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['data'][0]['permit_id'], 'P123')

    @patch('requests.get')
    def test_handle_api_error(self, mock_get):
        # Mock API error
        mock_get.return_value.status_code = 500
        mock_get.return_value.json.side_effect = Exception('API Error')

        result = self.collector.collect('test_town')
        self.assertFalse(result['success'])
        self.assertIn('error', result)

    def test_validate_permit_data(self):
        # Test valid permit data
        valid_permit = {
            'permit_id': 'P123',
            'type': 'building',
            'status': 'approved'
        }
        self.assertTrue(self.collector._validate_permit(valid_permit))

        # Test invalid permit data
        invalid_permit = {
            'type': 'building',  # Missing permit_id
            'status': 'approved'
        }
        self.assertFalse(self.collector._validate_permit(invalid_permit))

class TestTaxCollector(unittest.TestCase):
    def setUp(self):
        self.collector = TaxCollector()
        self.mock_response = {
            'records': [
                {
                    'parcel_id': 'T456',
                    'owner': 'John Doe',
                    'assessment': {
                        'land_value': 100000,
                        'building_value': 200000,
                        'total_value': 300000,
                        'assessment_year': 2024
                    }
                }
            ]
        }

    @patch('requests.get')
    def test_collect_tax_records(self, mock_get):
        # Mock successful API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_response

        result = self.collector.collect('test_town')
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['data'][0]['parcel_id'], 'T456')

    @patch('requests.get')
    def test_handle_rate_limit(self, mock_get):
        # Mock rate limit response
        mock_get.return_value.status_code = 429
        
        result = self.collector.collect('test_town')
        self.assertFalse(result['success'])
        self.assertIn('rate_limit', result['error'])

    def test_validate_tax_record(self):
        # Test valid tax record
        valid_record = {
            'parcel_id': 'T456',
            'owner': 'John Doe',
            'assessment': {
                'total_value': 300000
            }
        }
        self.assertTrue(self.collector._validate_record(valid_record))

        # Test invalid tax record
        invalid_record = {
            'owner': 'John Doe',  # Missing parcel_id
            'assessment': {
                'total_value': 300000
            }
        }
        self.assertFalse(self.collector._validate_record(invalid_record))

class TestUtilityCollector(unittest.TestCase):
    def setUp(self):
        self.collector = UtilityCollector()
        self.mock_response = {
            'utilities': [
                {
                    'property_id': 'U789',
                    'type': 'electric',
                    'usage': [
                        {
                            'date': '2025-01',
                            'amount': 1000,
                            'cost': 150.00
                        }
                    ]
                }
            ]
        }

    @patch('requests.get')
    def test_collect_utility_data(self, mock_get):
        # Mock successful API response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.mock_response

        result = self.collector.collect('test_town')
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 1)
        self.assertEqual(result['data'][0]['property_id'], 'U789')

    @patch('requests.get')
    def test_handle_missing_data(self, mock_get):
        # Mock missing data response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'utilities': []}

        result = self.collector.collect('test_town')
        self.assertTrue(result['success'])
        self.assertEqual(len(result['data']), 0)

    def test_validate_utility_data(self):
        # Test valid utility data
        valid_utility = {
            'property_id': 'U789',
            'type': 'electric',
            'usage': [
                {
                    'date': '2025-01',
                    'amount': 1000
                }
            ]
        }
        self.assertTrue(self.collector._validate_utility(valid_utility))

        # Test invalid utility data
        invalid_utility = {
            'type': 'electric',  # Missing property_id
            'usage': []
        }
        self.assertFalse(self.collector._validate_utility(invalid_utility))

if __name__ == '__main__':
    unittest.main()
