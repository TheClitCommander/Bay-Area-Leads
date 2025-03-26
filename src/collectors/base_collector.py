"""
Base collector module for data collection operations
"""
import logging
from abc import ABC, abstractmethod

class BaseCollector(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def collect(self):
        """Base collection method to be implemented by specific collectors"""
        pass
    
    def validate_data(self, data):
        """Basic validation of collected data"""
        if not data:
            self.logger.warning("No data collected")
            return False
        return True
