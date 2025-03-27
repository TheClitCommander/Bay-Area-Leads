#!/usr/bin/env python3
"""
PDF Date Extractor

Extracts auction dates, redemption deadlines, and other critical timeline information
from pre-foreclosure PDFs and legal notices.
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
import json

# Optional: If PyPDF2 is not available, provide instructions to install
try:
    from PyPDF2 import PdfReader
except ImportError:
    print("PyPDF2 not found. Please install it with: pip install PyPDF2")

logger = logging.getLogger(__name__)

class PdfDateExtractor:
    """
    Extract important dates from pre-foreclosure PDFs and legal notices.
    Uses pattern matching and NLP techniques to identify auction dates,
    redemption periods, and other critical timeline information.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the PDF date extractor.
        
        Args:
            config_file: Path to configuration file with patterns and settings
        """
        self.project_root = Path(__file__).parent.parent.parent
        
        # Load config
        if config_file:
            self.config_path = Path(config_file)
        else:
            self.config_path = self.project_root / 'config' / 'pdf_extractor_config.json'
        
        self.config = self._load_config()
        
        # Initialize date patterns
        self.date_patterns = [
            # Standard date formats
            r'(?:(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4})',
            r'(?:\d{1,2}/\d{1,2}/\d{2,4})',
            r'(?:\d{1,2}-\d{1,2}-\d{2,4})',
            r'(?:\d{1,2}\.\d{1,2}\.\d{2,4})',
        ]
        
        # Auction trigger phrases
        self.auction_triggers = [
            r'(?:public auction)',
            r'(?:foreclosure auction)',
            r'(?:foreclosure sale)',
            r'(?:auction date)',
            r'(?:sale date)',
            r'(?:to be sold at)',
            r'(?:will be sold at public auction)',
            r'(?:will sell at public auction)',
        ]
        
        # Redemption trigger phrases
        self.redemption_triggers = [
            r'(?:right to redeem)',
            r'(?:redemption period)',
            r'(?:right of redemption)',
            r'(?:may redeem until)',
            r'(?:redeem the property until)',
            r'(?:redeem on or before)',
        ]
        
        # Notice trigger phrases
        self.notice_triggers = [
            r'(?:notice of sale)',
            r'(?:notice of foreclosure)',
            r'(?:notice of default)',
            r'(?:notice of public sale)',
            r'(?:notice of trustee)',
        ]
        
        # Update with config patterns if available
        if self.config:
            if 'date_patterns' in self.config:
                self.date_patterns.extend(self.config['date_patterns'])
            if 'auction_triggers' in self.config:
                self.auction_triggers.extend(self.config['auction_triggers'])
            if 'redemption_triggers' in self.config:
                self.redemption_triggers.extend(self.config['redemption_triggers'])
            if 'notice_triggers' in self.config:
                self.notice_triggers.extend(self.config['notice_triggers'])
        
        # Compiled regex patterns
        self.date_regex = re.compile("|".join(self.date_patterns), re.IGNORECASE)
        
        logger.info("Initialized PDF Date Extractor")
    
    def _load_config(self) -> Optional[Dict[str, Any]]:
        """
        Load configuration file with patterns and settings.
        
        Returns:
            Configuration dictionary or None if file not found
        """
        if not self.config_path.exists():
            self._create_config_template()
            return None
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading PDF extractor config: {e}")
            return None
    
    def _create_config_template(self) -> None:
        """Create a template configuration file."""
        config_template = {
            "date_patterns": [
                # Add any state-specific or custom date formats here
            ],
            "auction_triggers": [
                # Add any state-specific auction phrases here
            ],
            "redemption_triggers": [
                # Add any state-specific redemption phrases here
            ],
            "notice_triggers": [
                # Add any state-specific notice phrases here
            ],
            "state_specific_rules": {
                "ME": {
                    "redemption_period_days": 90,
                    "typical_auction_delay_days": 30
                }
            }
        }
        
        try:
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_template, f, indent=2)
            
            logger.info(f"Created PDF extractor config template at {self.config_path}")
        except Exception as e:
            logger.error(f"Error creating PDF extractor config template: {e}")
    
    def extract_dates_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract important dates from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with extracted dates and related information
        """
        result = {
            'auction_date': None,
            'redemption_deadline': None,
            'notice_date': None,
            'all_dates': [],
            'confidence_score': 0.0,
            'days_until_auction': None,
            'days_until_redemption_deadline': None,
            'urgency_level': 'Unknown'
        }
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return result
        
        try:
            pdf_text = self._extract_text_from_pdf(pdf_path)
            if not pdf_text:
                logger.warning(f"No text content found in PDF: {pdf_path}")
                return result
            
            # Extract all dates
            all_dates = self._extract_all_dates(pdf_text)
            result['all_dates'] = all_dates
            
            # Extract auction date
            auction_date, auction_confidence = self._extract_auction_date(pdf_text, all_dates)
            if auction_date:
                result['auction_date'] = auction_date
                
                # Calculate days until auction
                days_until_auction = self._calculate_days_until(auction_date)
                if days_until_auction is not None:
                    result['days_until_auction'] = days_until_auction
            
            # Extract redemption deadline
            redemption_date, redemption_confidence = self._extract_redemption_deadline(pdf_text, all_dates, auction_date)
            if redemption_date:
                result['redemption_deadline'] = redemption_date
                
                # Calculate days until redemption deadline
                days_until_redemption = self._calculate_days_until(redemption_date)
                if days_until_redemption is not None:
                    result['days_until_redemption_deadline'] = days_until_redemption
            
            # Extract notice date (usually the earliest date in the document)
            notice_date, notice_confidence = self._extract_notice_date(pdf_text, all_dates)
            if notice_date:
                result['notice_date'] = notice_date
            
            # Calculate overall confidence score
            confidence_scores = [
                auction_confidence if auction_date else 0.0,
                redemption_confidence if redemption_date else 0.0,
                notice_confidence if notice_date else 0.0
            ]
            if confidence_scores:
                result['confidence_score'] = sum(confidence_scores) / len(confidence_scores)
            
            # Determine urgency level
            result['urgency_level'] = self._calculate_urgency_level(
                days_until_auction=result.get('days_until_auction'),
                days_until_redemption=result.get('days_until_redemption_deadline')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting dates from PDF {pdf_path}: {e}")
            return result
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content as a string
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PdfReader(f)
                text = ""
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                return text
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {e}")
            return ""
    
    def _extract_all_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract all dates from text.
        
        Args:
            text: Text content to extract dates from
            
        Returns:
            List of dictionaries with date information
        """
        dates = []
        
        # Find all date matches
        matches = list(self.date_regex.finditer(text))
        
        for match in matches:
            date_str = match.group(0)
            parsed_date = self._parse_date(date_str)
            
            if parsed_date:
                # Get surrounding context (50 chars before and after)
                start_idx = max(0, match.start() - 50)
                end_idx = min(len(text), match.end() + 50)
                context = text[start_idx:end_idx]
                
                dates.append({
                    'date_str': date_str,
                    'date_obj': parsed_date,
                    'position': match.start(),
                    'context': context
                })
        
        # Sort by position in document
        dates.sort(key=lambda x: x['position'])
        
        return dates
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string into datetime object.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Datetime object or None if parsing fails
        """
        date_formats = [
            # Full month name with comma
            "%B %d, %Y",
            "%B %dst, %Y", "%B %dnd, %Y", "%B %drd, %Y", "%B %dth, %Y",
            
            # Numeric formats
            "%m/%d/%Y", "%m/%d/%y",
            "%m-%d-%Y", "%m-%d-%y",
            "%m.%d.%Y", "%m.%d.%y",
        ]
        
        for fmt in date_formats:
            try:
                # Replace ordinals with just the number
                cleaned_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
                return datetime.strptime(cleaned_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_auction_date(self, text: str, all_dates: List[Dict[str, Any]]) -> Tuple[Optional[str], float]:
        """
        Extract auction date from text.
        
        Args:
            text: Text content to extract auction date from
            all_dates: List of all dates found in the text
            
        Returns:
            Tuple of (auction date string, confidence score)
        """
        # Create a list of auction trigger phrases with their regex patterns
        trigger_patterns = [(trigger, re.compile(trigger, re.IGNORECASE)) for trigger in self.auction_triggers]
        
        best_match = None
        best_confidence = 0.0
        
        # Look for dates that appear near auction trigger phrases
        for date_info in all_dates:
            context = date_info['context'].lower()
            date_position = 50  # Position of the date in the context
            
            for trigger, pattern in trigger_patterns:
                # Search for trigger in the context
                match = pattern.search(context)
                if match:
                    # Calculate distance between trigger and date
                    trigger_position = match.start()
                    distance = abs(trigger_position - date_position)
                    
                    # Calculate confidence based on distance (closer = higher confidence)
                    # Max distance we care about is 50 characters
                    distance_factor = max(0, 1 - (distance / 100))
                    
                    # Higher confidence for dates in the future
                    future_factor = 0.5
                    if date_info['date_obj'] > datetime.now():
                        future_factor = 1.0
                    
                    confidence = 0.7 * distance_factor + 0.3 * future_factor
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = date_info
        
        if best_match:
            return best_match['date_str'], best_confidence
        
        # Fallback: Look for future dates if no auction date was found
        future_dates = [d for d in all_dates if d['date_obj'] > datetime.now()]
        if future_dates:
            # Sort by date (nearest future date first)
            future_dates.sort(key=lambda x: x['date_obj'])
            return future_dates[0]['date_str'], 0.3
        
        return None, 0.0
    
    def _extract_redemption_deadline(self, text: str, all_dates: List[Dict[str, Any]], auction_date_str: Optional[str]) -> Tuple[Optional[str], float]:
        """
        Extract redemption deadline from text.
        
        Args:
            text: Text content to extract redemption deadline from
            all_dates: List of all dates found in the text
            auction_date_str: Extracted auction date string (if available)
            
        Returns:
            Tuple of (redemption deadline string, confidence score)
        """
        # Try to find explicit redemption deadline
        trigger_patterns = [(trigger, re.compile(trigger, re.IGNORECASE)) for trigger in self.redemption_triggers]
        
        best_match = None
        best_confidence = 0.0
        
        # Look for dates that appear near redemption trigger phrases
        for date_info in all_dates:
            context = date_info['context'].lower()
            date_position = 50  # Position of the date in the context
            
            for trigger, pattern in trigger_patterns:
                # Search for trigger in the context
                match = pattern.search(context)
                if match:
                    # Calculate distance between trigger and date
                    trigger_position = match.start()
                    distance = abs(trigger_position - date_position)
                    
                    # Calculate confidence based on distance (closer = higher confidence)
                    distance_factor = max(0, 1 - (distance / 100))
                    
                    # Higher confidence for dates in the future
                    future_factor = 0.5
                    if date_info['date_obj'] > datetime.now():
                        future_factor = 1.0
                    
                    confidence = 0.7 * distance_factor + 0.3 * future_factor
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = date_info
        
        if best_match:
            return best_match['date_str'], best_confidence
        
        # If auction date is available, estimate redemption deadline based on state rules
        if auction_date_str and self.config and 'state_specific_rules' in self.config:
            # Use default Maine rules if state not specified
            state_rules = self.config['state_specific_rules'].get('ME', {})
            redemption_period_days = state_rules.get('redemption_period_days', 90)
            
            # Parse auction date
            auction_date = None
            for date_info in all_dates:
                if date_info['date_str'] == auction_date_str:
                    auction_date = date_info['date_obj']
                    break
            
            if auction_date:
                # Calculate redemption deadline based on auction date
                redemption_date = auction_date - timedelta(days=redemption_period_days)
                
                # Format the date as a string (using the same format as the auction date)
                redemption_date_str = redemption_date.strftime("%B %d, %Y")
                
                return redemption_date_str, 0.4
        
        return None, 0.0
    
    def _extract_notice_date(self, text: str, all_dates: List[Dict[str, Any]]) -> Tuple[Optional[str], float]:
        """
        Extract notice date from text.
        
        Args:
            text: Text content to extract notice date from
            all_dates: List of all dates found in the text
            
        Returns:
            Tuple of (notice date string, confidence score)
        """
        trigger_patterns = [(trigger, re.compile(trigger, re.IGNORECASE)) for trigger in self.notice_triggers]
        
        best_match = None
        best_confidence = 0.0
        
        # Look for dates that appear near notice trigger phrases
        for date_info in all_dates:
            context = date_info['context'].lower()
            date_position = 50  # Position of the date in the context
            
            for trigger, pattern in trigger_patterns:
                # Search for trigger in the context
                match = pattern.search(context)
                if match:
                    # Calculate distance between trigger and date
                    trigger_position = match.start()
                    distance = abs(trigger_position - date_position)
                    
                    # Calculate confidence based on distance (closer = higher confidence)
                    distance_factor = max(0, 1 - (distance / 100))
                    confidence = distance_factor
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = date_info
        
        if best_match:
            return best_match['date_str'], best_confidence
        
        # Fallback: Use the earliest date in the document as notice date
        if all_dates:
            # Sort by date (earliest first)
            sorted_dates = sorted(all_dates, key=lambda x: x['date_obj'])
            return sorted_dates[0]['date_str'], 0.3
        
        return None, 0.0
    
    def _calculate_days_until(self, date_str: str) -> Optional[int]:
        """
        Calculate the number of days until a given date.
        
        Args:
            date_str: Date string
            
        Returns:
            Number of days until the date or None if parsing fails
        """
        parsed_date = self._parse_date(date_str)
        if not parsed_date:
            return None
        
        # Calculate days until date
        delta = parsed_date - datetime.now()
        return max(0, delta.days)
    
    def _calculate_urgency_level(self, days_until_auction: Optional[int], days_until_redemption: Optional[int]) -> str:
        """
        Calculate urgency level based on days until auction or redemption.
        
        Args:
            days_until_auction: Days until auction
            days_until_redemption: Days until redemption deadline
            
        Returns:
            Urgency level as string
        """
        # If both are None, we can't determine urgency
        if days_until_auction is None and days_until_redemption is None:
            return "Unknown"
        
        # Use the closest deadline to determine urgency
        days = None
        if days_until_auction is not None and days_until_redemption is not None:
            days = min(days_until_auction, days_until_redemption)
        elif days_until_auction is not None:
            days = days_until_auction
        else:
            days = days_until_redemption
        
        # Determine urgency level
        if days <= 7:
            return "Critical"
        elif days <= 14:
            return "High"
        elif days <= 30:
            return "Medium"
        else:
            return "Low"
    
    def update_lead_with_dates(self, lead: Dict[str, Any], pdf_path: str) -> Dict[str, Any]:
        """
        Extract dates from a PDF and update lead with date information.
        
        Args:
            lead: Lead dictionary to update
            pdf_path: Path to PDF file
            
        Returns:
            Updated lead dictionary
        """
        # Extract dates from PDF
        date_info = self.extract_dates_from_pdf(pdf_path)
        
        # Update lead with date information
        if date_info['auction_date']:
            lead['auction_date'] = date_info['auction_date']
        
        if date_info['redemption_deadline']:
            lead['redemption_deadline'] = date_info['redemption_deadline']
        
        if date_info['notice_date']:
            lead['notice_date'] = date_info['notice_date']
        
        if date_info['days_until_auction'] is not None:
            lead['days_until_auction'] = date_info['days_until_auction']
        
        if date_info['days_until_redemption_deadline'] is not None:
            lead['days_until_redemption'] = date_info['days_until_redemption_deadline']
        
        if date_info['urgency_level'] != "Unknown":
            lead['urgency_level'] = date_info['urgency_level']
        
        # Add date_confidence_score
        lead['date_confidence_score'] = date_info['confidence_score']
        
        return lead
    
    def process_lead_pdf_folder(self, lead_id: str, pdf_folder: str) -> Dict[str, Any]:
        """
        Process all PDFs in a folder for a specific lead.
        
        Args:
            lead_id: Lead ID to process
            pdf_folder: Folder containing PDF files
            
        Returns:
            Dictionary with extracted date information
        """
        result = {
            'auction_date': None,
            'redemption_deadline': None,
            'notice_date': None,
            'days_until_auction': None,
            'days_until_redemption': None,
            'urgency_level': 'Unknown',
            'date_confidence_score': 0.0,
            'processed_files': []
        }
        
        folder_path = Path(pdf_folder)
        if not folder_path.exists() or not folder_path.is_dir():
            logger.error(f"PDF folder not found: {pdf_folder}")
            return result
        
        # Find all PDF files in the folder
        pdf_files = list(folder_path.glob('*.pdf'))
        if not pdf_files:
            logger.warning(f"No PDF files found in folder: {pdf_folder}")
            return result
        
        # Process each PDF and keep the best results
        best_confidence = 0.0
        best_date_info = None
        
        for pdf_file in pdf_files:
            date_info = self.extract_dates_from_pdf(str(pdf_file))
            result['processed_files'].append(str(pdf_file))
            
            # Keep the result with highest confidence score
            if date_info['confidence_score'] > best_confidence:
                best_confidence = date_info['confidence_score']
                best_date_info = date_info
        
        # Update result with best date information
        if best_date_info:
            result['auction_date'] = best_date_info['auction_date']
            result['redemption_deadline'] = best_date_info['redemption_deadline']
            result['notice_date'] = best_date_info['notice_date']
            result['days_until_auction'] = best_date_info['days_until_auction']
            result['days_until_redemption'] = best_date_info['days_until_redemption_deadline']
            result['urgency_level'] = best_date_info['urgency_level']
            result['date_confidence_score'] = best_date_info['confidence_score']
        
        return result
    
    def get_urgency_score(self, days_until: Optional[int], max_days: int = 90) -> float:
        """
        Calculate urgency score (0.0-1.0) based on days until deadline.
        
        Args:
            days_until: Days until deadline (auction, redemption, etc.)
            max_days: Maximum number of days to consider (default: 90)
            
        Returns:
            Urgency score (0.0-1.0)
        """
        if days_until is None:
            return 0.0
        
        # Closer to the deadline = higher score
        score = 1.0 - (days_until / max_days)
        return max(0.0, min(1.0, score))
