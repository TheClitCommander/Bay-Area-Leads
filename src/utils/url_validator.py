"""
URL validation utility for property listings
"""
import re
import requests
from typing import Dict, List, Union
import logging

logger = logging.getLogger(__name__)

class URLValidator:
    def __init__(self):
        self.required_fields = {
            'basic_info': ['address', 'price', 'property_type', 'status'],
            'details': ['bedrooms', 'bathrooms', 'square_feet']
        }
    
    def validate_url(self, url: str) -> bool:
        """Validate if URL is properly formatted and accessible"""
        if not url:
            logger.error("URL is empty")
            return False
            
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
        if not url_pattern.match(url):
            logger.error(f"Invalid URL format: {url}")
            return False
            
        try:
            response = requests.head(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Error accessing URL {url}: {str(e)}")
            return False
    
    def validate_data_requirements(self, data: Dict) -> Dict[str, Union[bool, List[str]]]:
        """Validate if all required fields are present in the data"""
        missing_fields = []
        
        for category, fields in self.required_fields.items():
            if category not in data:
                missing_fields.extend([f"{category}.{field}" for field in fields])
                continue
                
            for field in fields:
                if field not in data[category]:
                    missing_fields.append(f"{category}.{field}")
        
        return {
            "is_valid": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }
    
    def validate_url_data(self, url_data: Dict) -> Dict[str, Union[bool, List[str]]]:
        """Validate URL data structure"""
        required_keys = ["listing_url", "source_type", "access_type"]
        missing_keys = [key for key in required_keys if key not in url_data]
        
        if missing_keys:
            return {
                "is_valid": False,
                "missing_fields": missing_keys
            }
        
        url_valid = self.validate_url(url_data["listing_url"])
        return {
            "is_valid": url_valid,
            "missing_fields": [] if url_valid else ["invalid_url"]
        }
