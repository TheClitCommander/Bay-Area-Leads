"""
Tests for TaxRecordCollector
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.collectors.tax_record_collector import TaxRecordCollector

class TestTaxRecordCollector(unittest.TestCase):
    def setUp(self):
        self.collector = TaxRecordCollector()
        
    def test_initialization(self):
        """Test collector initialization"""
        self.assertIsNotNone(self.collector.config)
        self.assertIsNotNone(self.collector.raw_data_path)
        
    def test_collect_with_valid_town(self):
        """Test collection with valid town name"""
        result = self.collector.collect('Brunswick')
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('metadata', result)
        
    def test_validate_data_with_valid_records(self):
        """Test data validation with valid records"""
        test_data = {
            'success': True,
            'data': [{
                'parcel_id': '123',
                'owner_name': 'John Doe',
                'property_address': '123 Main St'
            }]
        }
        self.assertTrue(self.collector.validate_data(test_data))
        
    def test_validate_data_with_invalid_records(self):
        """Test data validation with invalid records"""
        test_data = {
            'success': True,
            'data': [{
                'parcel_id': '123',
                # missing required fields
            }]
        }
        self.assertFalse(self.collector.validate_data(test_data))
        
if __name__ == '__main__':
    unittest.main()
