"""
Universal format processor for handling different data formats
"""
import logging
from typing import Dict, List, Union
from pathlib import Path
import pandas as pd
import tabula
import PyPDF2
from bs4 import BeautifulSoup
import re
import json
import csv
import xml.etree.ElementTree as ET

class FormatProcessor:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def process_content(self, content: Union[str, bytes], format_type: str = None, url: str = None) -> List[Dict]:
        """
        Process content regardless of format
        
        Args:
            content: Raw content to process
            format_type: Optional hint about content type
            url: Optional source URL to help determine format
            
        Returns:
            List of dictionaries containing extracted data
        """
        try:
            # Try to determine format if not provided
            if not format_type and url:
                format_type = self._detect_format_from_url(url)
            
            if not format_type:
                format_type = self._detect_format_from_content(content)
            
            # Process based on format
            if format_type == 'pdf':
                return self._process_pdf(content)
            elif format_type == 'html':
                return self._process_html(content)
            elif format_type == 'excel':
                return self._process_excel(content)
            elif format_type == 'csv':
                return self._process_csv(content)
            elif format_type == 'json':
                return self._process_json(content)
            elif format_type == 'xml':
                return self._process_xml(content)
            else:
                return self._process_text(content)
                
        except Exception as e:
            self.logger.error(f"Error processing content: {str(e)}")
            return []
    
    def _detect_format_from_url(self, url: str) -> str:
        """Detect format from URL"""
        url_lower = url.lower()
        if url_lower.endswith('.pdf'):
            return 'pdf'
        elif url_lower.endswith(('.xls', '.xlsx')):
            return 'excel'
        elif url_lower.endswith('.csv'):
            return 'csv'
        elif url_lower.endswith('.json'):
            return 'json'
        elif url_lower.endswith('.xml'):
            return 'xml'
        elif 'vision-government-solutions' in url_lower:
            return 'vision'
        elif 'trio' in url_lower:
            return 'trio'
        else:
            return 'html'
    
    def _detect_format_from_content(self, content: Union[str, bytes]) -> str:
        """Detect format from content"""
        if isinstance(content, bytes):
            if content.startswith(b'%PDF'):
                return 'pdf'
            elif content.startswith(b'PK'):
                return 'excel'
            content = content.decode('utf-8', errors='ignore')
            
        if content.strip().startswith('{'):
            return 'json'
        elif content.strip().startswith('<?xml'):
            return 'xml'
        elif content.strip().startswith(('<html', '<!DOCTYPE')):
            return 'html'
        elif ',' in content and content.count('\\n') > 0:
            return 'csv'
        return 'text'
    
    def _process_pdf(self, content: Union[str, bytes]) -> List[Dict]:
        """Process PDF content"""
        try:
            # Handle both file paths and raw content
            if isinstance(content, str) and Path(content).exists():
                # Extract tables
                tables = tabula.read_pdf(content, pages='all', multiple_tables=True)
                
                # Extract text
                with open(content, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text()
                
            else:
                # Handle raw PDF content
                # Would need to save to temp file first
                pass
                
            results = []
            # Convert tables to dicts
            for table in tables:
                results.extend(table.to_dict('records'))
                
            # Add any structured data found in text
            text_data = self._extract_structured_data(text)
            if text_data:
                results.append(text_data)
                
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            return []
    
    def _process_html(self, content: str) -> List[Dict]:
        """Process HTML content"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            results = []
            
            # Process tables
            for table in soup.find_all('table'):
                # Get headers
                headers = []
                for th in table.find_all('th'):
                    headers.append(th.text.strip())
                
                # If no headers, try first row
                if not headers:
                    first_row = table.find('tr')
                    if first_row:
                        headers = [td.text.strip() for td in first_row.find_all('td')]
                
                # Get data rows
                for row in table.find_all('tr')[1:]:
                    data = {}
                    for i, cell in enumerate(row.find_all('td')):
                        if i < len(headers):
                            data[headers[i]] = cell.text.strip()
                    if data:
                        results.append(data)
            
            # Process structured data in divs
            for div in soup.find_all('div', class_=re.compile(r'(detail|info|data)')):
                data = self._extract_structured_data(div.text)
                if data:
                    results.append(data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing HTML: {str(e)}")
            return []
    
    def _process_excel(self, content: Union[str, bytes]) -> List[Dict]:
        """Process Excel content"""
        try:
            # Read all sheets
            if isinstance(content, str):
                dfs = pd.read_excel(content, sheet_name=None)
            else:
                dfs = pd.read_excel(content, sheet_name=None)
            
            results = []
            for sheet_name, df in dfs.items():
                # Convert to list of dicts
                sheet_data = df.to_dict('records')
                for row in sheet_data:
                    row['sheet_name'] = sheet_name
                    results.append(row)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing Excel: {str(e)}")
            return []
    
    def _process_csv(self, content: Union[str, bytes]) -> List[Dict]:
        """Process CSV content"""
        try:
            if isinstance(content, str):
                if Path(content).exists():
                    df = pd.read_csv(content)
                else:
                    df = pd.read_csv(pd.StringIO(content))
            else:
                df = pd.read_csv(pd.StringIO(content.decode('utf-8')))
            
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Error processing CSV: {str(e)}")
            return []
    
    def _process_json(self, content: str) -> List[Dict]:
        """Process JSON content"""
        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error processing JSON: {str(e)}")
            return []
    
    def _process_xml(self, content: str) -> List[Dict]:
        """Process XML content"""
        try:
            root = ET.fromstring(content)
            results = []
            
            for child in root:
                data = {}
                for elem in child:
                    data[elem.tag] = elem.text
                results.append(data)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing XML: {str(e)}")
            return []
    
    def _extract_structured_data(self, text: str) -> Dict:
        """Extract structured data from text"""
        data = {}
        
        # Common patterns
        patterns = {
            'parcel_id': r'(?:Parcel|Map|Lot)\s*(?:ID|Number|#)?\s*[:=]?\s*([A-Z0-9-]+)',
            'address': r'(?:Location|Address|Property)\s*[:=]?\s*([0-9][^,\n]+)',
            'owner': r'(?:Owner|Name)\s*[:=]?\s*([^\n]+)',
            'value': r'(?:Value|Assessment|Amount)\s*[:=]?\s*\$?([\d,]+(?:\.\d{2})?)',
            'date': r'(?:Date|Recorded|Filed)\s*[:=]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                data[key] = match.group(1).strip()
        
        return data
