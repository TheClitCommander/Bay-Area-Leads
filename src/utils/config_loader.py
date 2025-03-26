"""
Configuration loader utility
"""
import os
import json
import logging
from pathlib import Path

class ConfigLoader:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_dir = Path(__file__).parent.parent.parent / 'config'
    
    def load_config(self, config_name):
        """Load configuration file"""
        config_path = self.config_dir / f"{config_name}.json"
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config {config_name}: {e}")
            return None
