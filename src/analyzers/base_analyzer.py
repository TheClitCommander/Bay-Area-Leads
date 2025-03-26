"""
Base analyzer module for data analysis operations
"""
import logging
from abc import ABC, abstractmethod

class BaseAnalyzer(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def analyze(self, data):
        """Base analysis method to be implemented by specific analyzers"""
        pass
    
    def validate_analysis(self, analysis_result):
        """Basic validation of analysis results"""
        if not analysis_result:
            self.logger.warning("No analysis results generated")
            return False
        return True
