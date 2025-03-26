"""
Base processor module for data processing operations
"""
import logging
from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def process(self, data):
        """Base processing method to be implemented by specific processors"""
        pass
    
    def validate_processed_data(self, data):
        """Basic validation of processed data"""
        if not data:
            self.logger.warning("No data processed")
            return False
        return True
