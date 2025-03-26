"""
VGSI-specific collector for property data from Vision Government Solutions
"""
import logging
import time
import random
from typing import Dict, List, Optional
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from .base_collector import BaseCollector

class VGSICollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://gis.vgsi.com/brunswickme/Default.aspx'
        self.driver = None
        self.wait = None
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Selenium WebDriver with Chrome"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Add additional options to avoid detection
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Add user agent
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute CDP commands to avoid detection
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                '''
            })
            
            self.wait = WebDriverWait(self.driver, 15)  # Increased timeout
            self.logger.info("WebDriver setup successful")
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {str(e)}")
            raise
            
    def collect(self, max_properties: int = 100) -> Dict:
        """
        Collect property data from VGSI
        
        Args:
            max_properties: Maximum number of properties to collect
            
        Returns:
            Dictionary containing collected property data
        """
        data = {
            'properties': [],
            'metadata': {
                'source': 'VGSI Brunswick',
                'timestamp': pd.Timestamp.now().isoformat(),
                'total_collected': 0
            }
        }
        
        try:
            self.driver.get(self.base_url)
            self._accept_terms()
            
            # Start with street search
            properties = self._collect_by_street(max_properties)
            data['properties'].extend(properties)
            data['metadata']['total_collected'] = len(properties)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting VGSI data: {str(e)}")
            return data
        finally:
            self.cleanup()
            
    def _accept_terms(self):
        """Accept terms and conditions if present"""
        try:
            accept_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btnAccept"))
            )
            accept_button.click()
            time.sleep(2)  # Wait for page to load
        except TimeoutException:
            self.logger.info("No terms acceptance needed")
            
    def _collect_by_street(self, max_properties: int) -> List[Dict]:
        """Collect properties by searching street by street"""
        properties = []
        try:
            # Navigate to search page with delay
            time.sleep(2)
            
            # Click street search with retry
            for attempt in range(3):
                try:
                    street_search = self.wait.until(
                        EC.element_to_be_clickable((By.ID, "btnStreetSearch"))
                    )
                    street_search.click()
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    time.sleep(2)
            
            # Get list of streets with retry
            for attempt in range(3):
                try:
                    street_select = self.wait.until(
                        EC.presence_of_element_located((By.ID, "ddlStreet"))
                    )
                    streets = [option.text for option in street_select.find_elements(By.TAG_NAME, "option")]
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    time.sleep(2)
            
            # Process streets with random delays
            for street in streets[1:]:  # Skip first empty option
                if len(properties) >= max_properties:
                    break
                
                # Add random delay between streets
                time.sleep(2 + random.random() * 2)
                
                street_properties = self._collect_street_properties(street)
                if street_properties:
                    properties.extend(street_properties)
                    self.logger.info(f"Collected {len(properties)} properties so far")
                
        except Exception as e:
            self.logger.error(f"Error in street collection: {str(e)}")
            if 'timeout' in str(e).lower():
                self.logger.info("Attempting to refresh session...")
                self.refresh_session()
            
        return properties
        
    def _collect_street_properties(self, street: str) -> List[Dict]:
        """Collect all properties for a given street"""
        properties = []
        try:
            # Select street
            street_select = self.wait.until(
                EC.presence_of_element_located((By.ID, "ddlStreet"))
            )
            street_select.send_keys(street)
            
            # Click search
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "btnSearch"))
            )
            search_button.click()
            
            # Get property links
            property_links = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[href*='Parcel.aspx']"))
            )
            
            for link in property_links:
                property_data = self._collect_property_details(link.get_attribute('href'))
                if property_data:
                    properties.append(property_data)
                    
        except Exception as e:
            self.logger.error(f"Error collecting street {street}: {str(e)}")
            
        return properties
        
    def _collect_property_details(self, property_url: str) -> Optional[Dict]:
        """Collect details for a specific property"""
        try:
            self.driver.get(property_url)
            time.sleep(1)  # Wait for page load
            
            # Extract property details
            details = {
                'parcel_id': self._safe_get_text("lblParcelID"),
                'location': self._safe_get_text("lblLocation"),
                'owner': self._safe_get_text("lblOwner"),
                'assessment': self._safe_get_text("lblTotal"),
                'land_area': self._safe_get_text("lblLandArea"),
                'property_type': self._safe_get_text("lblUseCode"),
                'year_built': self._safe_get_text("lblYearBuilt"),
                'url': property_url
            }
            
            return details
            
        except Exception as e:
            self.logger.error(f"Error collecting property details: {str(e)}")
            return None
            
    def _safe_get_text(self, element_id: str) -> str:
        """Safely get text from an element"""
        try:
            element = self.driver.find_element(By.ID, element_id)
            return element.text.strip()
        except NoSuchElementException:
            return ""
            
    def refresh_session(self):
        """Refresh the browser session when encountering issues"""
        try:
            self.logger.info("Refreshing browser session...")
            self.cleanup()
            time.sleep(5)  # Wait before starting new session
            self.setup_driver()
            self.driver.get(self.base_url)
            time.sleep(2)
            self._accept_terms()
        except Exception as e:
            self.logger.error(f"Error refreshing session: {str(e)}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {str(e)}")
                
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()
