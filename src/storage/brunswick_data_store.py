"""
SQLite-based storage system for Brunswick data with data cleaning and normalization
"""
import sqlite3
from typing import Dict, List, Optional, Tuple
import json
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path
import usaddress
import re
from dataclasses import dataclass
from contextlib import contextmanager

@dataclass
class CleaningResult:
    original: Dict
    cleaned: Dict
    changes: List[str]
    warnings: List[str]

class BrunswickDataStore:
    def __init__(self, db_path: str = "brunswick_data.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database and cache schemas
        self.table_schemas = {}
        self._init_database()
        self._cache_schemas()
        
    @contextmanager
    def get_connection(self):
        """Get a database connection with row factory set to return dictionaries"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def _init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create businesses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    address TEXT NOT NULL,
                    founding_date TEXT,
                    license_status TEXT,
                    license_number TEXT,
                    health_inspection INTEGER,
                    food_license INTEGER,
                    neighborhood TEXT,
                    last_updated TEXT
                )
            """)
            
            # Create properties table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id TEXT PRIMARY KEY,
                    map_lot TEXT NOT NULL,
                    address TEXT NOT NULL,
                    type TEXT NOT NULL,
                    zoning TEXT NOT NULL,
                    assessment REAL,
                    neighborhood TEXT,
                    permit_status TEXT,
                    permit_type TEXT,
                    permit_value REAL,
                    last_updated TEXT
                )
            """)
            
            # Create licenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS licenses (
                    id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    license_number TEXT NOT NULL,
                    type TEXT NOT NULL,
                    issue_date TEXT,
                    expiration_date TEXT,
                    status TEXT,
                    FOREIGN KEY (business_id) REFERENCES businesses (id)
                )
            """)
            
            conn.commit()
        
    def initialize_tables(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create businesses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    address TEXT NOT NULL,
                    founding_date TEXT,
                    license_status TEXT,
                    license_number TEXT,
                    health_inspection INTEGER,
                    food_license INTEGER,
                    neighborhood TEXT,
                    last_updated TEXT
                )
            """)
            
            # Create properties table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id TEXT PRIMARY KEY,
                    map_lot TEXT NOT NULL,
                    address TEXT NOT NULL,
                    type TEXT NOT NULL,
                    zoning TEXT NOT NULL,
                    assessment REAL,
                    neighborhood TEXT,
                    permit_status TEXT,
                    permit_type TEXT,
                    permit_value REAL,
                    last_updated TEXT
                )
            """)
            
            # Create licenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS licenses (
                    id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    license_number TEXT NOT NULL,
                    type TEXT NOT NULL,
                    issue_date TEXT,
                    expiration_date TEXT,
                    status TEXT,
                    FOREIGN KEY (business_id) REFERENCES businesses (id)
                )
            """)
            
            conn.commit()
            
    def _cache_schemas(self):
        """Cache table schemas for efficient access"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for table in ['businesses', 'properties', 'licenses']:
                cursor.execute(f"PRAGMA table_info({table})")
                self.table_schemas[table] = {row[1]: row[2].upper() for row in cursor.fetchall()}
            
    def insert(self, table: str, data: Dict):
        """Insert data into a table"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get schema for the table
            table_schema = self.table_schemas.get(table)
            if not table_schema:
                raise ValueError(f"Unknown table: {table}")
            
            # Filter data to only include existing columns
            filtered_data = {k: v for k, v in data.items() if k in table_schema}
            
            # Check for missing required columns
            cursor.execute(f"PRAGMA table_info({table})")
            required_columns = [row[1] for row in cursor.fetchall() if row[3]]
            missing_columns = [col for col in required_columns if col not in filtered_data]
            
            if missing_columns:
                self.logger.error(f"Missing required columns for {table}: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            if not filtered_data:
                self.logger.warning(f"No valid columns found for table {table}")
                return
            
            # Only convert None values to NULL and booleans to integers
            for k, v in filtered_data.items():
                if v is None:
                    continue
                elif isinstance(v, bool):
                    filtered_data[k] = 1 if v else 0
            
            # Build the insert query
            cols = list(filtered_data.keys())
            placeholders = ', '.join(['?' for _ in cols])
            cols_str = ', '.join(cols)
            query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
            
            try:
                # Execute the query
                self.logger.debug(f"Executing query: {query} with values {list(filtered_data.values())}")
                cursor.execute(query, list(filtered_data.values()))
                conn.commit()
            except sqlite3.Error as e:
                self.logger.error(f"Error inserting into {table}: {e}\nQuery: {query}\nValues: {filtered_data}")
                raise
        
        # Address normalization patterns
        self.address_patterns = {
            'street_types': {
                'ST': 'STREET',
                'RD': 'ROAD',
                'AVE': 'AVENUE',
                'DR': 'DRIVE',
                'LN': 'LANE',
                'CT': 'COURT',
                'CIR': 'CIRCLE',
                'BLVD': 'BOULEVARD',
                'HWY': 'HIGHWAY'
            },
            'directions': {
                'N': 'NORTH',
                'S': 'SOUTH',
                'E': 'EAST',
                'W': 'WEST',
                'NE': 'NORTHEAST',
                'NW': 'NORTHWEST',
                'SE': 'SOUTHEAST',
                'SW': 'SOUTHWEST'
            }
        }
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def _init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Businesses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    normalized_name TEXT,
                    address TEXT,
                    normalized_address TEXT,
                    phone TEXT,
                    website TEXT,
                    category TEXT,
                    source TEXT,
                    last_updated TIMESTAMP,
                    raw_data JSON,
                    UNIQUE(normalized_name, normalized_address)
                )
            """)
            
            # Properties table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    map_lot TEXT UNIQUE,
                    address TEXT,
                    normalized_address TEXT,
                    tax_account TEXT,
                    assessment REAL,
                    zoning TEXT,
                    last_updated TIMESTAMP,
                    raw_data JSON
                )
            """)
            
            # Permits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS permits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    permit_number TEXT UNIQUE,
                    type TEXT,
                    status TEXT,
                    issue_date DATE,
                    expiration_date DATE,
                    property_id INTEGER,
                    business_id INTEGER,
                    raw_data JSON,
                    FOREIGN KEY(property_id) REFERENCES properties(id),
                    FOREIGN KEY(business_id) REFERENCES businesses(id)
                )
            """)
            
            # Address normalization table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS address_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_address TEXT UNIQUE,
                    normalized_address TEXT,
                    components JSON,
                    last_updated TIMESTAMP
                )
            """)
            
            conn.commit()
            
    def store_business(self, business_data: Dict) -> Tuple[int, CleaningResult]:
        """Store cleaned business data"""
        # Clean and normalize business data
        cleaning_result = self._clean_business_data(business_data)
        cleaned_data = cleaning_result.cleaned
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO businesses (
                        name, normalized_name, address, normalized_address,
                        phone, website, category, source, last_updated, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (normalized_name, normalized_address) 
                    DO UPDATE SET
                        phone = excluded.phone,
                        website = excluded.website,
                        category = excluded.category,
                        source = excluded.source,
                        last_updated = excluded.last_updated,
                        raw_data = excluded.raw_data
                    RETURNING id
                """, (
                    cleaned_data['name'],
                    cleaned_data['normalized_name'],
                    cleaned_data['address'],
                    cleaned_data['normalized_address'],
                    cleaned_data.get('phone'),
                    cleaned_data.get('website'),
                    cleaned_data.get('category'),
                    cleaned_data.get('source'),
                    datetime.now().isoformat(),
                    json.dumps(business_data)
                ))
                
                business_id = cursor.fetchone()[0]
                conn.commit()
                return business_id, cleaning_result
                
            except Exception as e:
                self.logger.error(f"Error storing business: {e}")
                conn.rollback()
                raise
                
    def store_property(self, property_data: Dict) -> Tuple[int, CleaningResult]:
        """Store cleaned property data"""
        # Clean and normalize property data
        cleaning_result = self._clean_property_data(property_data)
        cleaned_data = cleaning_result.cleaned
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO properties (
                        map_lot, address, normalized_address,
                        tax_account, assessment, zoning,
                        last_updated, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (map_lot) 
                    DO UPDATE SET
                        address = excluded.address,
                        normalized_address = excluded.normalized_address,
                        tax_account = excluded.tax_account,
                        assessment = excluded.assessment,
                        zoning = excluded.zoning,
                        last_updated = excluded.last_updated,
                        raw_data = excluded.raw_data
                    RETURNING id
                """, (
                    cleaned_data['map_lot'],
                    cleaned_data['address'],
                    cleaned_data['normalized_address'],
                    cleaned_data.get('tax_account'),
                    cleaned_data.get('assessment'),
                    cleaned_data.get('zoning'),
                    datetime.now().isoformat(),
                    json.dumps(property_data)
                ))
                
                property_id = cursor.fetchone()[0]
                conn.commit()
                return property_id, cleaning_result
                
            except Exception as e:
                self.logger.error(f"Error storing property: {e}")
                conn.rollback()
                raise
                
    def store_permit(self, permit_data: Dict) -> Tuple[int, CleaningResult]:
        """Store cleaned permit data"""
        # Clean permit data
        cleaning_result = self._clean_permit_data(permit_data)
        cleaned_data = cleaning_result.cleaned
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO permits (
                        permit_number, type, status,
                        issue_date, expiration_date,
                        property_id, business_id, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (permit_number) 
                    DO UPDATE SET
                        type = excluded.type,
                        status = excluded.status,
                        issue_date = excluded.issue_date,
                        expiration_date = excluded.expiration_date,
                        property_id = excluded.property_id,
                        business_id = excluded.business_id,
                        raw_data = excluded.raw_data
                    RETURNING id
                """, (
                    cleaned_data['permit_number'],
                    cleaned_data['type'],
                    cleaned_data['status'],
                    cleaned_data.get('issue_date'),
                    cleaned_data.get('expiration_date'),
                    cleaned_data.get('property_id'),
                    cleaned_data.get('business_id'),
                    json.dumps(permit_data)
                ))
                
                permit_id = cursor.fetchone()[0]
                conn.commit()
                return permit_id, cleaning_result
                
            except Exception as e:
                self.logger.error(f"Error storing permit: {e}")
                conn.rollback()
                raise
                
    def _clean_business_data(self, data: Dict) -> CleaningResult:
        """Clean and normalize business data"""
        original = data.copy()
        cleaned = {}
        changes = []
        warnings = []
        
        # Clean business name
        if name := data.get('name'):
            cleaned['name'] = name.strip()
            cleaned['normalized_name'] = self._normalize_business_name(name)
            if cleaned['name'] != name:
                changes.append(f"Cleaned business name: {name} -> {cleaned['name']}")
                
        # Normalize address
        if address := data.get('address'):
            cleaned_address = self._normalize_address(address)
            cleaned['address'] = cleaned_address.get('formatted_address')
            cleaned['normalized_address'] = cleaned_address.get('normalized_address')
            if cleaned['address'] != address:
                changes.append(f"Normalized address: {address} -> {cleaned['address']}")
                
        # Clean phone number
        if phone := data.get('phone'):
            cleaned['phone'] = self._clean_phone_number(phone)
            if cleaned['phone'] != phone:
                changes.append(f"Cleaned phone: {phone} -> {cleaned['phone']}")
                
        # Clean website
        if website := data.get('website'):
            cleaned['website'] = self._clean_url(website)
            if cleaned['website'] != website:
                changes.append(f"Cleaned website: {website} -> {cleaned['website']}")
                
        # Copy other fields
        cleaned.update({
            k: v for k, v in data.items()
            if k not in cleaned and v is not None
        })
        
        return CleaningResult(original, cleaned, changes, warnings)
        
    def _clean_property_data(self, data: Dict) -> CleaningResult:
        """Clean and normalize property data"""
        original = data.copy()
        cleaned = {}
        changes = []
        warnings = []
        
        # Clean map-lot
        if map_lot := data.get('map_lot'):
            cleaned['map_lot'] = self._clean_map_lot(map_lot)
            if cleaned['map_lot'] != map_lot:
                changes.append(f"Cleaned map-lot: {map_lot} -> {cleaned['map_lot']}")
                
        # Normalize address
        if address := data.get('address'):
            cleaned_address = self._normalize_address(address)
            cleaned['address'] = cleaned_address.get('formatted_address')
            cleaned['normalized_address'] = cleaned_address.get('normalized_address')
            if cleaned['address'] != address:
                changes.append(f"Normalized address: {address} -> {cleaned['address']}")
                
        # Clean assessment value
        if assessment := data.get('assessment'):
            try:
                cleaned['assessment'] = float(str(assessment).replace('$', '').replace(',', ''))
                if str(cleaned['assessment']) != str(assessment):
                    changes.append(f"Cleaned assessment: {assessment} -> {cleaned['assessment']}")
            except ValueError:
                warnings.append(f"Invalid assessment value: {assessment}")
                
        # Copy other fields
        cleaned.update({
            k: v for k, v in data.items()
            if k not in cleaned and v is not None
        })
        
        return CleaningResult(original, cleaned, changes, warnings)
        
    def _clean_permit_data(self, data: Dict) -> CleaningResult:
        """Clean permit data"""
        original = data.copy()
        cleaned = {}
        changes = []
        warnings = []
        
        # Clean permit number
        if permit_number := data.get('permit_number'):
            cleaned['permit_number'] = permit_number.strip().upper()
            if cleaned['permit_number'] != permit_number:
                changes.append(f"Cleaned permit number: {permit_number} -> {cleaned['permit_number']}")
                
        # Clean dates
        for date_field in ['issue_date', 'expiration_date']:
            if date_value := data.get(date_field):
                try:
                    cleaned[date_field] = pd.to_datetime(date_value).strftime('%Y-%m-%d')
                    if cleaned[date_field] != date_value:
                        changes.append(f"Cleaned {date_field}: {date_value} -> {cleaned[date_field]}")
                except ValueError:
                    warnings.append(f"Invalid {date_field}: {date_value}")
                    
        # Normalize status
        if status := data.get('status'):
            cleaned['status'] = self._normalize_permit_status(status)
            if cleaned['status'] != status:
                changes.append(f"Normalized status: {status} -> {cleaned['status']}")
                
        # Copy other fields
        cleaned.update({
            k: v for k, v in data.items()
            if k not in cleaned and v is not None
        })
        
        return CleaningResult(original, cleaned, changes, warnings)
        
    def _normalize_address(self, address: str) -> Dict:
        """Normalize address format"""
        try:
            # Parse address
            components, address_type = usaddress.tag(address)
            
            # Standardize components
            street_number = components.get('AddressNumber', '')
            street_name = components.get('StreetName', '').upper()
            street_type = components.get('StreetNamePostType', '').upper()
            unit = components.get('OccupancyIdentifier', '')
            
            # Normalize street type
            if street_type in self.address_patterns['street_types']:
                street_type = self.address_patterns['street_types'][street_type]
                
            # Build normalized address
            parts = [
                street_number,
                street_name,
                street_type,
                f"UNIT {unit}" if unit else None,
                "BRUNSWICK",
                "ME"
            ]
            
            normalized = ' '.join(p for p in parts if p)
            
            return {
                'normalized_address': normalized,
                'formatted_address': f"{street_number} {street_name} {street_type}".title(),
                'components': components
            }
            
        except Exception as e:
            self.logger.error(f"Error normalizing address: {e}")
            return {'normalized_address': address, 'formatted_address': address, 'components': {}}
            
    def _normalize_business_name(self, name: str) -> str:
        """Normalize business name"""
        # Remove common business suffixes
        suffixes = ['LLC', 'INC', 'CORP', 'LTD', 'CO', 'COMPANY']
        normalized = name.upper()
        for suffix in suffixes:
            normalized = re.sub(rf'\b{suffix}\b\.?', '', normalized)
            
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        normalized = ' '.join(normalized.split())
        
        return normalized
        
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number"""
        # Remove non-numeric characters
        digits = re.sub(r'\D', '', phone)
        
        # Ensure 10 digits
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        return phone
        
    def _clean_url(self, url: str) -> str:
        """Clean and normalize URL"""
        url = url.lower().strip()
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        return url
        
    def _clean_map_lot(self, map_lot: str) -> str:
        """Clean map-lot format"""
        # Remove spaces and normalize format
        cleaned = re.sub(r'\s+', '', map_lot.upper())
        # Ensure proper format (e.g., "123-A-45")
        if match := re.match(r'^(\d+)-([A-Z])-(\d+)$', cleaned):
            return cleaned
        return map_lot
        
    def _normalize_permit_status(self, status: str) -> str:
        """Normalize permit status"""
        status_map = {
            'ACTIVE': ['ACTIVE', 'CURRENT', 'VALID'],
            'PENDING': ['PENDING', 'IN REVIEW', 'SUBMITTED'],
            'EXPIRED': ['EXPIRED', 'TERMINATED', 'CLOSED'],
            'APPROVED': ['APPROVED', 'GRANTED', 'ISSUED'],
            'DENIED': ['DENIED', 'REJECTED', 'REFUSED']
        }
        
        status = status.upper()
        for normalized, variants in status_map.items():
            if status in variants:
                return normalized
        return status
