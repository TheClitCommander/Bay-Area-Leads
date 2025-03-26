"""
Advanced extractors for specialized data sources
"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime
import json
from dataclasses import dataclass
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .site_specific_extractors import BaseExtractor, ExtractedData
import pandas as pd
import numpy as np
from PIL import Image
import pytesseract
import io
import requests
from urllib.parse import urljoin, urlparse
import os

class PDFExtractor(BaseExtractor):
    """Extractor for PDF documents with advanced OCR capabilities"""
    
    def __init__(self, session: aiohttp.ClientSession, driver=None):
        super().__init__(session, driver)
        self.tesseract_config = r'--oem 3 --psm 6'
        
    async def can_handle(self, url: str) -> bool:
        return url.lower().endswith('.pdf')
        
    async def extract(self, url: str, soup: BeautifulSoup) -> ExtractedData:
        try:
            # Download PDF
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None
                    
                pdf_content = await response.read()
                
            # Convert PDF to images
            images = await self._pdf_to_images(pdf_content)
            
            # Process each image
            results = []
            for idx, image in enumerate(images):
                # Extract text via OCR
                text = pytesseract.image_to_string(
                    image,
                    config=self.tesseract_config
                )
                
                # Detect tables
                tables = await self._extract_tables(image)
                
                # Detect forms
                forms = await self._detect_forms(image)
                
                results.append({
                    'page': idx + 1,
                    'text': text,
                    'tables': tables,
                    'forms': forms
                })
                
            return ExtractedData(
                source="PDF",
                data_type="document",
                content=results,
                metadata={'url': url}
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF data: {e}")
            return None
            
    async def _extract_tables(self, image) -> List[Dict]:
        """Extract tables from image using advanced detection"""
        tables = []
        try:
            # Convert to grayscale
            gray = image.convert('L')
            
            # Use pytesseract to detect table structure
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz|-.,$% "'
            data = pytesseract.image_to_data(
                gray,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Analyze text positions to detect table structures
            tables = self._analyze_table_structure(data)
            
        except Exception as e:
            self.logger.error(f"Error extracting tables: {e}")
            
        return tables

class ZillowExtractor(BaseExtractor):
    """Extractor for Zillow property data"""
    
    async def can_handle(self, url: str) -> bool:
        return 'zillow.com' in url
        
    async def extract(self, url: str, soup: BeautifulSoup) -> ExtractedData:
        data = {
            'property_info': {},
            'price_history': [],
            'tax_history': [],
            'schools': [],
            'neighborhood': {}
        }
        
        try:
            if self.driver:
                # Wait for dynamic content
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-testid='home-details-summary']")
                    )
                )
                
                # Extract property details
                data['property_info'] = await self._extract_property_info()
                
                # Extract price history
                data['price_history'] = await self._extract_price_history()
                
                # Extract tax history
                data['tax_history'] = await self._extract_tax_history()
                
                # Extract school information
                data['schools'] = await self._extract_schools()
                
                # Extract neighborhood data
                data['neighborhood'] = await self._extract_neighborhood()
                
            return ExtractedData(
                source="Zillow",
                data_type="property_details",
                content=data,
                metadata={'url': url}
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting Zillow data: {e}")
            return None
            
    async def _extract_property_info(self) -> Dict:
        """Extract detailed property information"""
        info = {}
        try:
            # Basic details
            summary = self.driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='home-details-summary']"
            )
            info['summary'] = summary.text
            
            # Facts and features
            facts = self.driver.find_elements(
                By.CSS_SELECTOR,
                "[data-testid='facts-list'] > li"
            )
            for fact in facts:
                label = fact.find_element(By.CSS_SELECTOR, ".fact-label").text
                value = fact.find_element(By.CSS_SELECTOR, ".fact-value").text
                info[label.lower().replace(' ', '_')] = value
                
        except Exception as e:
            self.logger.error(f"Error extracting property info: {e}")
            
        return info

class RealtyTracExtractor(BaseExtractor):
    """Extractor for RealtyTrac foreclosure data"""
    
    async def can_handle(self, url: str) -> bool:
        return 'realtytrac.com' in url
        
    async def extract(self, url: str, soup: BeautifulSoup) -> ExtractedData:
        data = {
            'property_info': {},
            'foreclosure_status': {},
            'auction_details': {},
            'tax_info': {},
            'market_stats': {}
        }
        
        try:
            if self.driver:
                # Extract property information
                data['property_info'] = await self._extract_property_details()
                
                # Extract foreclosure status
                data['foreclosure_status'] = await self._extract_foreclosure_status()
                
                # Extract auction details if available
                data['auction_details'] = await self._extract_auction_details()
                
                # Extract tax information
                data['tax_info'] = await self._extract_tax_info()
                
                # Extract market statistics
                data['market_stats'] = await self._extract_market_stats()
                
            return ExtractedData(
                source="RealtyTrac",
                data_type="foreclosure_details",
                content=data,
                metadata={'url': url}
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting RealtyTrac data: {e}")
            return None

class RedfinExtractor(BaseExtractor):
    """Extractor for Redfin property data"""
    
    async def can_handle(self, url: str) -> bool:
        return 'redfin.com' in url
        
    async def extract(self, url: str, soup: BeautifulSoup) -> ExtractedData:
        data = {
            'property_info': {},
            'price_insights': {},
            'property_history': [],
            'schools': [],
            'walk_score': {},
            'climate_risk': {}
        }
        
        try:
            if self.driver:
                # Extract property details
                data['property_info'] = await self._extract_property_details()
                
                # Extract price insights
                data['price_insights'] = await self._extract_price_insights()
                
                # Extract property history
                data['property_history'] = await self._extract_property_history()
                
                # Extract school information
                data['schools'] = await self._extract_schools()
                
                # Extract walk score
                data['walk_score'] = await self._extract_walk_score()
                
                # Extract climate risk data
                data['climate_risk'] = await self._extract_climate_risk()
                
            return ExtractedData(
                source="Redfin",
                data_type="property_details",
                content=data,
                metadata={'url': url}
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting Redfin data: {e}")
            return None

class TownExtractor(BaseExtractor):
    """Enhanced extractor for town/city websites"""
    
    def __init__(self, session: aiohttp.ClientSession, driver=None):
        super().__init__(session, driver)
        self.town_patterns = {
            'bath': {
                'domain': 'cityofbath.com',
                'patterns': {
                    'property': r'/assessor|/property',
                    'permits': r'/permits|/codes',
                    'planning': r'/planning|/zoning',
                    'meetings': r'/meetings|/agenda',
                    'documents': r'/documents|/records'
                }
            },
            'topsham': {
                'domain': 'topshammaine.com',
                'patterns': {
                    'property': r'/assessing|/property',
                    'permits': r'/codes|/permits',
                    'planning': r'/planning|/development',
                    'meetings': r'/meetings|/calendar',
                    'documents': r'/documents|/forms'
                }
            },
            'harpswell': {
                'domain': 'harpswell.maine.gov',
                'patterns': {
                    'property': r'/assessing|/property',
                    'permits': r'/codes|/permits',
                    'planning': r'/planning|/development',
                    'meetings': r'/meetings|/calendar',
                    'documents': r'/documents|/forms'
                }
            },
            'freeport': {
                'domain': 'freeportmaine.com',
                'patterns': {
                    'property': r'/assessor|/property',
                    'permits': r'/permits|/codes',
                    'planning': r'/planning|/zoning',
                    'meetings': r'/meetings|/agenda',
                    'documents': r'/documents|/records'
                }
            }
        }
        
    async def can_handle(self, url: str) -> bool:
        return any(
            pattern['domain'] in url 
            for pattern in self.town_patterns.values()
        )
        
    async def extract(self, url: str, soup: BeautifulSoup) -> ExtractedData:
        # Identify town
        town = next(
            (name for name, pattern in self.town_patterns.items()
             if pattern['domain'] in url),
            None
        )
        
        if not town:
            return None
            
        # Determine content type
        patterns = self.town_patterns[town]['patterns']
        content_type = next(
            (ctype for ctype, pattern in patterns.items()
             if re.search(pattern, url)),
            'general'
        )
        
        # Extract based on content type
        if content_type == 'property':
            return await self._extract_property_data(url, soup, town)
        elif content_type == 'permits':
            return await self._extract_permit_data(url, soup, town)
        elif content_type == 'planning':
            return await self._extract_planning_data(url, soup, town)
        elif content_type == 'meetings':
            return await self._extract_meeting_data(url, soup, town)
        elif content_type == 'documents':
            return await self._extract_document_data(url, soup, town)
        else:
            return await self._extract_general_data(url, soup, town)
            
    async def _extract_property_data(
        self,
        url: str,
        soup: BeautifulSoup,
        town: str
    ) -> ExtractedData:
        """Extract property-related data"""
        data = {
            'assessments': [],
            'tax_maps': [],
            'property_cards': [],
            'recent_sales': []
        }
        
        try:
            if self.driver:
                # Extract assessment data
                assessment_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "[class*='assessment'], [class*='property']"
                )
                for element in assessment_elements:
                    assessment = {
                        'title': element.get_attribute('title'),
                        'link': element.get_attribute('href'),
                        'description': element.text
                    }
                    data['assessments'].append(assessment)
                    
                # Extract tax maps
                map_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "a[href*='map'], a[href*='gis']"
                )
                for element in map_elements:
                    map_data = {
                        'title': element.get_attribute('title'),
                        'link': element.get_attribute('href'),
                        'type': 'pdf' if '.pdf' in element.get_attribute('href') else 'web'
                    }
                    data['tax_maps'].append(map_data)
                    
                # Extract property cards
                card_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "a[href*='card'], a[href*='property-record']"
                )
                for element in card_elements:
                    card = {
                        'title': element.get_attribute('title'),
                        'link': element.get_attribute('href'),
                        'date': element.get_attribute('data-date')
                    }
                    data['property_cards'].append(card)
                    
                # Extract recent sales
                sales_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "[class*='sales'], [class*='transfer']"
                )
                for element in sales_elements:
                    sale = {
                        'date': element.get_attribute('data-date'),
                        'price': element.get_attribute('data-price'),
                        'address': element.get_attribute('data-address'),
                        'type': element.get_attribute('data-type')
                    }
                    data['recent_sales'].append(sale)
                    
            return ExtractedData(
                source=f"{town.title()}Gov",
                data_type="property_data",
                content=data,
                metadata={'url': url}
            )
            
        except Exception as e:
            self.logger.error(f"Error extracting property data: {e}")
            return None
