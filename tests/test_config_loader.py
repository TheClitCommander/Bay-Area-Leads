"""
Test configuration loader
"""
import unittest
from src.utils.config_loader import ConfigLoader

class TestConfigLoader(unittest.TestCase):
    def setUp(self):
        self.config_loader = ConfigLoader()
    
    def test_load_config(self):
        config = self.config_loader.load_config('settings')
        self.assertIsNotNone(config)
        self.assertIn('data_sources', config)
        self.assertIn('processing', config)
        self.assertIn('analysis', config)

if __name__ == '__main__':
    unittest.main()
