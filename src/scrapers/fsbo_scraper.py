"""
FSBO Scraper Module

This module implements scrapers for For Sale By Owner (FSBO) listings from
various sources including Craigslist and Facebook Marketplace.
"""

import os
import sys
import re
import json
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.scrapers.scraper_base import ScraperBase, LeadData

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FSBOScraper")


class CraigslistScraper(ScraperBase):
    """
    Scraper for FSBO listings from Craigslist
    """
    
    def __init__(
        self,
        base_url: str = "https://maine.craigslist.org",
        search_area: str = "brunswick",  # Options: portland, maine, brunswick, etc.
        search_radius: int = 25,  # Miles
        **kwargs
    ):
        """
        Initialize the Craigslist scraper
        
        Args:
            base_url: Base URL for Craigslist
            search_area: Area to search within
            search_radius: Search radius in miles
            **kwargs: Additional arguments to pass to ScraperBase
        """
        super().__init__(name="craigslist_fsbo", **kwargs)
        
        self.base_url = base_url
        self.search_area = search_area
        self.search_radius = search_radius
        
        # Define search parameters
        self.search_params = {
            "query": "fsbo OR \"for sale by owner\" OR \"off market\" OR \"off-market\"",
            "min_price": 100000,
            "max_price": 1000000,
            "search_distance": search_radius,
            "postal": "04011",  # Brunswick zip code
            "sale_date": "all+dates"
        }
        
        self.headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        self.logger.info(f"Initialized Craigslist FSBO scraper for {search_area}")
    
    def _build_search_url(self) -> str:
        """Build the search URL with parameters"""
        search_url = f"{self.base_url}/search/rea"
        
        # Add location filter if specified
        if self.search_area and self.search_area != "maine":
            search_url = f"{self.base_url}/search/{self.search_area}/rea"
        
        # Append query parameters
        query_parts = []
        for key, value in self.search_params.items():
            if value is not None:
                query_parts.append(f"{key}={value}")
        
        if query_parts:
            search_url += "?" + "&".join(query_parts)
        
        return search_url
    
    def run(self, max_pages: int = 5, max_listings: int = 100) -> List[Dict]:
        """
        Run the Craigslist FSBO scraper
        
        Args:
            max_pages: Maximum number of pages to scrape
            max_listings: Maximum number of listings to scrape
            
        Returns:
            List of normalized lead data dictionaries
        """
        self.logger.info(f"Starting Craigslist FSBO scraper")
        leads = []
        processed_count = 0
        
        search_url = self._build_search_url()
        self.logger.info(f"Search URL: {search_url}")
        
        # Scrape listing pages
        for page in range(max_pages):
            # Modify URL for pagination
            page_url = search_url
            if page > 0:
                page_url = f"{search_url}&s={page * 120}"  # Craigslist uses 120 items per page
            
            self.logger.info(f"Scraping page {page + 1} at {page_url}")
            
            try:
                # Get the page content
                response = requests.get(page_url, headers=self.headers)
                response.raise_for_status()
                
                # Parse the HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all listing items
                listings = soup.select('li.result-row')
                
                if not listings:
                    self.logger.info(f"No more listings found on page {page + 1}")
                    break
                
                self.logger.info(f"Found {len(listings)} listings on page {page + 1}")
                
                # Process each listing
                for listing in listings:
                    # Extract listing ID
                    data_id = listing.get('data-pid')
                    
                    if not data_id or self.is_processed(data_id):
                        continue
                    
                    try:
                        # Find the listing URL
                        link_elem = listing.select_one('a.result-title')
                        if not link_elem:
                            continue
                        
                        listing_url = link_elem.get('href')
                        listing_title = link_elem.text.strip()
                        
                        # Extract basic data from listing preview
                        price_elem = listing.select_one('.result-price')
                        price_text = price_elem.text.strip() if price_elem else None
                        price = self._extract_price(price_text) if price_text else None
                        
                        # Extract date
                        date_elem = listing.select_one('.result-date')
                        date_text = date_elem.get('datetime') if date_elem else None
                        listing_date = datetime.fromisoformat(date_text) if date_text else datetime.now()
                        
                        # Extract location
                        location_elem = listing.select_one('.result-hood')
                        location = location_elem.text.strip('()') if location_elem else None
                        
                        # Get detailed listing data
                        listing_data = self._scrape_listing_details(listing_url)
                        
                        if listing_data:
                            # Create normalized lead data
                            lead_data = self._create_lead_data(
                                data_id, 
                                listing_url, 
                                listing_title, 
                                price, 
                                listing_date, 
                                location, 
                                listing_data
                            )
                            
                            leads.append(lead_data.to_dict())
                            self.mark_processed(data_id, {
                                'url': listing_url,
                                'title': listing_title,
                                'price': price
                            })
                            
                            processed_count += 1
                            if processed_count >= max_listings:
                                self.logger.info(f"Reached maximum number of listings ({max_listings})")
                                break
                    
                    except Exception as e:
                        self.logger.error(f"Error processing listing {data_id}: {e}")
                
                if processed_count >= max_listings:
                    break
                
                # Add delay between pages
                self.random_delay(2.0, 5.0)
            
            except Exception as e:
                self.logger.error(f"Error scraping page {page + 1}: {e}")
                break
        
        # Save cache
        self.save_cache()
        
        # Save leads to file
        if leads:
            self.save_leads(leads)
        
        self.logger.info(f"Completed Craigslist FSBO scraper. Found {len(leads)} new leads")
        return leads
    
    def _scrape_listing_details(self, listing_url: str) -> Dict:
        """
        Scrape detailed information from a listing page
        
        Args:
            listing_url: URL of the listing page
            
        Returns:
            Dictionary of listing details
        """
        try:
            # Get the listing page
            self.headers["User-Agent"] = self.get_random_user_agent()
            response = requests.get(listing_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract listing details
            listing_data = {}
            
            # Get main content
            content_elem = soup.select_one('#postingbody')
            listing_data['description'] = content_elem.text.strip() if content_elem else None
            
            # Get attributes table
            attrs = {}
            attr_groups = soup.select('.attrgroup')
            for group in attr_groups:
                spans = group.select('span')
                for span in spans:
                    # Check if it's a key-value pair
                    if ':' in span.text:
                        key, value = [s.strip() for s in span.text.split(':', 1)]
                        attrs[key.lower()] = value
                    else:
                        # It's a single attribute like "3BR / 2Ba"
                        text = span.text.strip()
                        # Try to extract bedrooms/bathrooms
                        br_match = re.search(r'(\d+)BR', text)
                        ba_match = re.search(r'(\d+)Ba', text)
                        if br_match:
                            attrs['bedrooms'] = int(br_match.group(1))
                        if ba_match:
                            attrs['bathrooms'] = int(ba_match.group(1))
            
            listing_data['attributes'] = attrs
            
            # Get images
            images = []
            image_elems = soup.select('#thumbs a')
            for img_elem in image_elems:
                img_url = img_elem.get('href')
                if img_url:
                    images.append(img_url)
            
            listing_data['images'] = images
            
            # Get map data if available
            map_elem = soup.select_one('#map')
            if map_elem:
                latitude = map_elem.get('data-latitude')
                longitude = map_elem.get('data-longitude')
                
                if latitude and longitude:
                    listing_data['latitude'] = float(latitude)
                    listing_data['longitude'] = float(longitude)
            
            # Get contact info
            contact_elem = soup.select_one('.reply_options')
            listing_data['contact_info'] = {}
            if contact_elem:
                # Look for phone number
                phone_match = re.search(r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})', 
                                      response.text)
                if phone_match:
                    listing_data['contact_info']['phone'] = phone_match.group(1)
                
                # Look for email - Craigslist obfuscates emails, so this is tricky
                email_elem = contact_elem.select_one('[data-email]')
                if email_elem:
                    listing_data['contact_info']['email'] = email_elem.get('data-email')
            
            return listing_data
        
        except Exception as e:
            self.logger.error(f"Error scraping listing details at {listing_url}: {e}")
            return {}
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from price text"""
        if not price_text:
            return None
        
        # Remove non-numeric characters except decimal point
        price_str = re.sub(r'[^\d.]', '', price_text)
        try:
            return float(price_str)
        except (ValueError, TypeError):
            return None
    
    def _create_lead_data(
        self, 
        listing_id: str, 
        listing_url: str, 
        title: str, 
        price: Optional[float], 
        listing_date: datetime, 
        location: Optional[str], 
        details: Dict
    ) -> LeadData:
        """
        Create a standardized LeadData object from Craigslist listing data
        
        Args:
            listing_id: Craigslist listing ID
            listing_url: URL of the listing
            title: Listing title
            price: Listing price
            listing_date: Date the listing was posted
            location: Location from listing
            details: Detailed listing data
            
        Returns:
            LeadData object
        """
        # Extract attributes
        attrs = details.get('attributes', {})
        
        # Try to parse address from title and description
        full_text = f"{title} {details.get('description', '')}"
        address = self._extract_address(full_text, location)
        
        # Extract bedrooms and bathrooms
        bedrooms = attrs.get('bedrooms')
        if not bedrooms:
            bed_match = re.search(r'(\d+)\s*bed', full_text, re.IGNORECASE)
            if bed_match:
                bedrooms = int(bed_match.group(1))
        
        bathrooms = attrs.get('bathrooms')
        if not bathrooms:
            bath_match = re.search(r'(\d+(?:\.\d+)?)\s*bath', full_text, re.IGNORECASE)
            if bath_match:
                bathrooms = float(bath_match.group(1))
        
        # Extract square footage
        sqft = attrs.get('sqft') or attrs.get('square feet') or attrs.get('area')
        if not sqft:
            sqft_match = re.search(r'(\d+)\s*sq\s*\.?\s*ft', full_text, re.IGNORECASE)
            if sqft_match:
                sqft = int(sqft_match.group(1))
        
        if isinstance(sqft, str):
            sqft = self._extract_numeric_value(sqft)
        
        # Extract year built
        year_built = attrs.get('year built') or attrs.get('year')
        if isinstance(year_built, str):
            year_match = re.search(r'(\d{4})', year_built)
            if year_match:
                year_built = int(year_match.group(1))
        
        if not year_built:
            year_match = re.search(r'built\s+in\s+(\d{4})', full_text, re.IGNORECASE)
            if year_match:
                year_built = int(year_match.group(1))
        
        # Determine property type
        property_type = attrs.get('housing type') or attrs.get('property type')
        if not property_type:
            type_indicators = {
                'house': ['house', 'home', 'single family', 'single-family'],
                'condo': ['condo', 'condominium'],
                'apartment': ['apartment', 'apt', 'unit'],
                'land': ['land', 'lot', 'acre', 'acres'],
                'multi-family': ['multi family', 'multi-family', 'duplex', 'triplex']
            }
            
            for p_type, indicators in type_indicators.items():
                if any(ind.lower() in full_text.lower() for ind in indicators):
                    property_type = p_type
                    break
        
        # Calculate urgency score based on various factors
        urgency = self._calculate_urgency(full_text, title, details, listing_date)
        
        # Create lead data
        return LeadData(
            source="craigslist",
            source_id=listing_id,
            address=address.get('full_address') if address else None,
            city=address.get('city') if address else None,
            state=address.get('state') if address else 'ME',  # Default to Maine
            zip_code=address.get('zip_code') if address else None,
            price=price,
            listing_date=listing_date,
            description=details.get('description'),
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            square_feet=sqft,
            lot_size=self._extract_lot_size(full_text, attrs),
            year_built=year_built,
            property_type=property_type,
            images=details.get('images', []),
            contact_info=details.get('contact_info', {}),
            raw_data={
                'url': listing_url,
                'title': title,
                'location': location,
                'attributes': attrs,
                'coordinates': {
                    'latitude': details.get('latitude'),
                    'longitude': details.get('longitude')
                }
            },
            urgency=urgency
        )
    
    def _extract_address(self, text: str, location: Optional[str]) -> Optional[Dict]:
        """
        Extract address components from text
        
        Args:
            text: Text to search for address
            location: Location hint from listing
            
        Returns:
            Dictionary of address components or None
        """
        # Common Maine cities
        maine_cities = [
            'portland', 'lewiston', 'bangor', 'auburn', 'biddeford', 
            'sanford', 'brunswick', 'augusta', 'south portland', 'waterville',
            'westbrook', 'bath', 'saco', 'falmouth', 'topsham', 'freeport',
            'yarmouth', 'scarborough', 'gorham', 'rockland', 'camden'
        ]
        
        # Street address patterns
        address_pattern = r'\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct|Circle|Cir|Trail|Trl|Highway|Hwy|Route|Rt)'
        
        # ZIP code pattern
        zip_pattern = r'(?<!\d)0[0-8]\d{3}(?!\d)'  # Maine ZIP codes
        
        address_match = re.search(address_pattern, text, re.IGNORECASE)
        zip_match = re.search(zip_pattern, text)
        
        address_parts = {}
        
        # Extract street address
        if address_match:
            address_parts['street_address'] = address_match.group(0)
        
        # Extract ZIP code
        if zip_match:
            address_parts['zip_code'] = zip_match.group(0)
        
        # Extract city
        for city in maine_cities:
            city_pattern = r'\b' + re.escape(city) + r'\b'
            if re.search(city_pattern, text, re.IGNORECASE):
                address_parts['city'] = city.title()
                break
        
        # If no city found but location hint exists, try to extract city from that
        if 'city' not in address_parts and location:
            for city in maine_cities:
                if city.lower() in location.lower():
                    address_parts['city'] = city.title()
                    break
        
        # Default state to Maine
        address_parts['state'] = 'ME'
        
        # Build full address
        if address_parts:
            full_address_parts = []
            
            if 'street_address' in address_parts:
                full_address_parts.append(address_parts['street_address'])
            
            location_parts = []
            if 'city' in address_parts:
                location_parts.append(address_parts['city'])
            if 'state' in address_parts:
                location_parts.append(address_parts['state'])
            if 'zip_code' in address_parts:
                location_parts.append(address_parts['zip_code'])
            
            if location_parts:
                full_address_parts.append(', '.join(location_parts))
            
            if full_address_parts:
                address_parts['full_address'] = ', '.join(full_address_parts)
        
        return address_parts if address_parts else None
    
    def _extract_lot_size(self, text: str, attrs: Dict) -> Optional[float]:
        """Extract lot size in acres from text and attributes"""
        # Check if it's in attributes
        lot_size = attrs.get('lot size') or attrs.get('acres')
        
        if lot_size:
            return self._extract_numeric_value(lot_size)
        
        # Try to find in text
        acre_patterns = [
            r'(\d+(?:\.\d+)?)\s*acres',
            r'(\d+(?:\.\d+)?)\s*acre',
            r'lot\s+size\s*:\s*(\d+(?:\.\d+)?)',
            r'lot\s+size\s+(\d+(?:\.\d+)?)\s*acres'
        ]
        
        for pattern in acre_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, TypeError):
                    pass
        
        return None
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract numeric value from text"""
        if not text:
            return None
        
        # Extract digits and decimal point
        num_str = re.sub(r'[^\d.]', '', text)
        
        # Handle case where there might be multiple decimal points
        parts = num_str.split('.')
        if len(parts) > 2:
            num_str = parts[0] + '.' + parts[1]
        
        try:
            return float(num_str)
        except (ValueError, TypeError):
            return None
    
    def _calculate_urgency(self, text: str, title: str, details: Dict, listing_date: datetime) -> int:
        """
        Calculate urgency score (0-10) based on listing factors
        
        Args:
            text: Full text of listing
            title: Listing title
            details: Detailed listing data
            listing_date: Date the listing was posted
            
        Returns:
            Urgency score (0-10)
        """
        score = 0
        
        # Recent listings are more urgent
        days_old = (datetime.now() - listing_date).days
        if days_old < 1:
            score += 3
        elif days_old < 3:
            score += 2
        elif days_old < 7:
            score += 1
        
        # Keywords indicating motivation
        urgent_keywords = [
            'urgent', 'must sell', 'need to sell', 'quick sale', 'motivated',
            'relocating', 'below market', 'reduced', 'price drop', 'bargain',
            'divorce', 'estate sale', 'inherited', 'foreclosure', 'cash only',
            'fixer', 'needs work', 'as is', 'under market', 'priced to sell'
        ]
        
        keyword_count = sum(1 for keyword in urgent_keywords if keyword.lower() in text.lower())
        score += min(4, keyword_count)  # Cap at 4 points
        
        # If price is mentioned in title, might be more motivated
        if re.search(r'\$\d+', title):
            score += 1
        
        # If contact info is provided, easier to reach
        if details.get('contact_info', {}).get('phone'):
            score += 1
        
        # If multiple images, more serious seller
        image_count = len(details.get('images', []))
        if image_count > 10:
            score += 1
        
        # Cap at 10
        return min(10, score)
    
    def normalize_data(self, raw_data: Dict) -> Dict:
        """
        Normalize Craigslist data to standard format
        Used for external integration with raw data
        
        Args:
            raw_data: Raw Craigslist listing data
            
        Returns:
            Normalized lead data dictionary
        """
        lead = self._create_lead_data(
            raw_data.get('id', ''),
            raw_data.get('url', ''),
            raw_data.get('title', ''),
            raw_data.get('price'),
            raw_data.get('date', datetime.now()),
            raw_data.get('location'),
            raw_data
        )
        
        return lead.to_dict()


# Wrapper class for all FSBO scrapers
class FSBOScraper:
    """
    Main class to run all FSBO scrapers
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        use_craigslist: bool = True,
        use_facebook: bool = False,  # Facebook is harder, so default to False
        config: Optional[Dict] = None
    ):
        """
        Initialize the FSBO scraper
        
        Args:
            output_dir: Directory for output files
            use_craigslist: Whether to use Craigslist scraper
            use_facebook: Whether to use Facebook scraper
            config: Configuration dictionary
        """
        self.logger = logging.getLogger("FSBOScraper")
        self.output_dir = output_dir
        self.use_craigslist = use_craigslist
        self.use_facebook = use_facebook
        self.config = config or {}
        
        # Initialize scrapers
        self.scrapers = []
        
        if use_craigslist:
            craigslist_config = self.config.get('craigslist', {})
            self.scrapers.append(CraigslistScraper(
                output_dir=output_dir,
                **craigslist_config
            ))
        
        if use_facebook:
            # Facebook scraper would be initialized here
            # This would use Playwright or Puppeteer
            self.logger.info("Facebook scraper not yet implemented")
        
        self.logger.info(f"Initialized FSBO scraper with {len(self.scrapers)} active scrapers")
    
    def run(self) -> Dict[str, List[Dict]]:
        """
        Run all FSBO scrapers
        
        Returns:
            Dictionary of leads by source
        """
        self.logger.info("Starting FSBO scraper")
        all_leads = {}
        
        for scraper in self.scrapers:
            try:
                self.logger.info(f"Running {scraper.name} scraper")
                leads = scraper.run()
                all_leads[scraper.name] = leads
                self.logger.info(f"{scraper.name} found {len(leads)} leads")
            except Exception as e:
                self.logger.error(f"Error running {scraper.name} scraper: {e}")
        
        # Combine all leads into a single file
        if all_leads:
            combined_leads = []
            for source_leads in all_leads.values():
                combined_leads.extend(source_leads)
            
            if combined_leads:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Path(self.output_dir) if self.output_dir else project_root / 'data' / 'leads'
                output_path.mkdir(parents=True, exist_ok=True)
                
                with open(output_path / f"fsbo_leads_{timestamp}.json", 'w') as f:
                    json.dump(combined_leads, f, indent=2)
                
                self.logger.info(f"Saved {len(combined_leads)} combined leads")
        
        self.logger.info("Completed FSBO scraper")
        return all_leads


def main():
    """Run the FSBO scraper as a standalone script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape FSBO listings')
    parser.add_argument('--output-dir', help='Output directory for lead files')
    parser.add_argument('--use-craigslist', action='store_true', default=True, help='Use Craigslist scraper')
    parser.add_argument('--use-facebook', action='store_true', help='Use Facebook scraper')
    parser.add_argument('--config', help='Path to configuration file')
    args = parser.parse_args()
    
    # Load config if provided
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
    
    # Initialize and run scraper
    scraper = FSBOScraper(
        output_dir=args.output_dir,
        use_craigslist=args.use_craigslist,
        use_facebook=args.use_facebook,
        config=config
    )
    
    leads = scraper.run()
    
    # Print summary
    total_leads = sum(len(source_leads) for source_leads in leads.values())
    print(f"Found {total_leads} total leads:")
    for source, source_leads in leads.items():
        print(f"  - {source}: {len(source_leads)} leads")


if __name__ == "__main__":
    main()
