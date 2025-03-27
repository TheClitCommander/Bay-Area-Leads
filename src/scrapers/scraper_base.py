"""
Base Scraper Module

This module defines the base classes and common utilities for all lead generation scrapers.
"""

import os
import sys
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class ScraperBase(ABC):
    """
    Base class for all lead generation scrapers
    """
    
    def __init__(
        self,
        name: str,
        output_dir: Optional[str] = None,
        cache_dir: Optional[str] = None,
        config: Optional[Dict] = None,
        user_agents: Optional[List[str]] = None
    ):
        """
        Initialize the base scraper
        
        Args:
            name: Name of the scraper
            output_dir: Directory for output files
            cache_dir: Directory for cache files
            config: Configuration dictionary
            user_agents: List of user agents to rotate through
        """
        self.name = name
        self.logger = logging.getLogger(f"Scraper.{name}")
        
        # Set up data directories
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = project_root / 'data' / 'leads' / name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = project_root / 'data' / 'cache' / name
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config
        self.config = config or {}
        
        # Set up user agents for rotation
        default_user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0'
        ]
        self.user_agents = user_agents or default_user_agents
        
        # Initialize cache
        self._init_cache()
        
        self.logger.info(f"Initialized {name} scraper")
    
    def _init_cache(self):
        """Initialize the cache system"""
        self.cache_file = self.cache_dir / 'processed_items.json'
        
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.processed_cache = json.load(f)
                self.logger.info(f"Loaded {len(self.processed_cache)} items from cache")
            except Exception as e:
                self.logger.error(f"Error loading cache: {e}")
                self.processed_cache = {}
        else:
            self.processed_cache = {}
    
    def save_cache(self):
        """Save the processed items cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.processed_cache, f)
            self.logger.info(f"Saved {len(self.processed_cache)} items to cache")
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
    
    def is_processed(self, item_id: str) -> bool:
        """Check if an item has already been processed"""
        return item_id in self.processed_cache
    
    def mark_processed(self, item_id: str, metadata: Optional[Dict] = None):
        """Mark an item as processed"""
        self.processed_cache[item_id] = {
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
    
    def get_random_user_agent(self) -> str:
        """Get a random user agent from the list"""
        return random.choice(self.user_agents)
    
    def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 5.0):
        """Add a random delay to avoid rate limiting"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def save_leads(self, leads: List[Dict], filename: Optional[str] = None):
        """Save leads to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name}_leads_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        try:
            with open(output_path, 'w') as f:
                json.dump(leads, f, indent=2)
            self.logger.info(f"Saved {len(leads)} leads to {output_path}")
            return str(output_path)
        except Exception as e:
            self.logger.error(f"Error saving leads: {e}")
            return None
    
    @abstractmethod
    def run(self, *args, **kwargs):
        """Run the scraper"""
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: Dict) -> Dict:
        """Normalize scraped data to standard format"""
        pass


class LeadData:
    """
    Standard data structure for all lead types
    """
    
    def __init__(
        self,
        source: str,
        source_id: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        price: Optional[float] = None,
        listing_date: Optional[datetime] = None,
        description: Optional[str] = None,
        bedrooms: Optional[int] = None,
        bathrooms: Optional[float] = None,
        square_feet: Optional[int] = None,
        lot_size: Optional[float] = None,
        year_built: Optional[int] = None,
        property_type: Optional[str] = None,
        images: Optional[List[str]] = None,
        contact_info: Optional[Dict] = None,
        raw_data: Optional[Dict] = None,
        status: str = "new",
        urgency: int = 0  # 0-10 scale, higher is more urgent
    ):
        """
        Initialize a standard lead data object
        
        Args:
            source: Source of the lead (e.g., "craigslist", "facebook", "court")
            source_id: Unique identifier from the source
            address: Property address
            city: Property city
            state: Property state
            zip_code: Property zip code
            price: Listing price
            listing_date: Date the property was listed
            description: Property description
            bedrooms: Number of bedrooms
            bathrooms: Number of bathrooms
            square_feet: Property square footage
            lot_size: Lot size (acres)
            year_built: Year the property was built
            property_type: Type of property
            images: List of image URLs
            contact_info: Dict of contact information
            raw_data: Original raw data from source
            status: Status of the lead
            urgency: Urgency score (0-10)
        """
        self.source = source
        self.source_id = source_id
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.price = price
        self.listing_date = listing_date
        self.description = description
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.square_feet = square_feet
        self.lot_size = lot_size
        self.year_built = year_built
        self.property_type = property_type
        self.images = images or []
        self.contact_info = contact_info or {}
        self.raw_data = raw_data or {}
        self.status = status
        self.urgency = urgency
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert lead data to dictionary"""
        return {
            'source': self.source,
            'source_id': self.source_id,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'price': self.price,
            'listing_date': self.listing_date.isoformat() if self.listing_date else None,
            'description': self.description,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'square_feet': self.square_feet,
            'lot_size': self.lot_size,
            'year_built': self.year_built,
            'property_type': self.property_type,
            'images': self.images,
            'contact_info': self.contact_info,
            'status': self.status,
            'urgency': self.urgency,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LeadData':
        """Create a LeadData object from a dictionary"""
        lead = cls(
            source=data.get('source', ''),
            source_id=data.get('source_id', ''),
        )
        
        # Set all other attributes
        for key, value in data.items():
            if key in ['created_at', 'updated_at', 'listing_date'] and value:
                try:
                    setattr(lead, key, datetime.fromisoformat(value))
                except (ValueError, TypeError):
                    pass
            else:
                setattr(lead, key, value)
        
        return lead
