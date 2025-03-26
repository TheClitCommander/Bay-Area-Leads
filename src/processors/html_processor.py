"""
HTML and PDF processor for public records
"""
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import pandas as pd
import tabula
import re

class HTMLProcessor:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_table_data(self, html_content: str, table_identifiers: Dict[str, str]) -> List[Dict]:
        """
        Extract data from HTML tables using identifiers
        
        Args:
            html_content: Raw HTML content
            table_identifiers: Dict of column identifiers to look for
            
        Returns:
            List of dictionaries containing extracted data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # Find all tables in the HTML
            tables = soup.find_all('table')
            
            for table in tables:
                # Extract headers
                headers = []
                for th in table.find_all('th'):
                    headers.append(th.text.strip())
                
                # If no headers found, try first row
                if not headers:
                    first_row = table.find('tr')
                    if first_row:
                        headers = [td.text.strip() for td in first_row.find_all('td')]
                
                # Map headers to our expected fields
                header_map = {}
                for expected_field, possible_names in table_identifiers.items():
                    for i, header in enumerate(headers):
                        if any(name.lower() in header.lower() for name in possible_names):
                            header_map[i] = expected_field
                
                # Extract data rows
                for row in table.find_all('tr')[1:]:  # Skip header row
                    cells = row.find_all('td')
                    if cells:
                        data = {}
                        for i, cell in enumerate(cells):
                            if i in header_map:
                                data[header_map[i]] = cell.text.strip()
                        if data:
                            results.append(data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error extracting table data: {str(e)}")
            return []

    def extract_pdf_tables(self, pdf_path: str) -> List[Dict]:
        """
        Extract tables from PDF files
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dictionaries containing extracted data
        """
        try:
            # Extract tables from PDF
            tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
            
            results = []
            for df in tables:
                # Convert DataFrame to dict
                records = df.to_dict('records')
                results.extend(records)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF tables: {str(e)}")
            return []

    def clean_extracted_data(self, data: List[Dict]) -> List[Dict]:
        """
        Clean and standardize extracted data
        
        Args:
            data: List of dictionaries containing raw data
            
        Returns:
            List of dictionaries with cleaned data
        """
        cleaned_data = []
        
        for record in data:
            cleaned_record = {}
            
            for key, value in record.items():
                if isinstance(value, str):
                    # Remove extra whitespace
                    value = ' '.join(value.split())
                    
                    # Try to convert numbers
                    if self._looks_like_money(value):
                        value = self._convert_money_string(value)
                    elif self._looks_like_number(value):
                        value = self._convert_number_string(value)
                
                cleaned_record[key] = value
            
            cleaned_data.append(cleaned_record)
        
        return cleaned_data

    def _looks_like_money(self, value: str) -> bool:
        """Check if string looks like a money value"""
        return bool(re.match(r'^\$?[\d,]+\.?\d*$', value.strip()))

    def _looks_like_number(self, value: str) -> bool:
        """Check if string looks like a number"""
        return bool(re.match(r'^[\d,]+\.?\d*$', value.strip()))

    def _convert_money_string(self, value: str) -> float:
        """Convert money string to float"""
        try:
            return float(value.replace('$', '').replace(',', ''))
        except ValueError:
            return 0.0

    def _convert_number_string(self, value: str) -> float:
        """Convert number string to float"""
        try:
            return float(value.replace(',', ''))
        except ValueError:
            return 0.0
