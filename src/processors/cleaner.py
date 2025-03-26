"""
Data cleaning and standardization pipeline
"""
import logging
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
import re

from ..utils.address_standardizer import standardize_address
from ..utils.name_standardizer import standardize_name

class DataCleaner:
    """
    Cleans and standardizes property data
    Handles:
    1. Missing values
    2. Data type conversion
    3. Format standardization
    4. Duplicate removal
    5. Outlier detection
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Configure cleaning rules
        self.rules = {
            'property': {
                'address': self._clean_address,
                'city': self._clean_city,
                'state': self._clean_state,
                'zipcode': self._clean_zipcode,
                'year_built': self._clean_year,
                'square_feet': self._clean_numeric,
                'lot_size': self._clean_numeric,
                'bedrooms': self._clean_integer,
                'bathrooms': self._clean_numeric,
                'units': self._clean_integer,
                'land_value': self._clean_currency,
                'building_value': self._clean_currency,
                'total_value': self._clean_currency
            },
            'owner': {
                'name': self._clean_name,
                'mailing_address': self._clean_address,
                'owner_type': self._clean_owner_type
            },
            'transaction': {
                'price': self._clean_currency,
                'seller': self._clean_name,
                'buyer': self._clean_name,
                'date': self._clean_date
            },
            'permit': {
                'estimated_cost': self._clean_currency,
                'final_cost': self._clean_currency,
                'issue_date': self._clean_date,
                'expiration_date': self._clean_date,
                'completed_date': self._clean_date
            }
        }

    def clean(self, data: Dict, data_type: str) -> Dict:
        """
        Clean and standardize a data record
        """
        try:
            if not isinstance(data, dict):
                return data
            
            # Get rules for this data type
            type_rules = self.rules.get(data_type, {})
            
            # Clean each field
            cleaned = {}
            for field, value in data.items():
                # Get cleaning function for this field
                clean_func = type_rules.get(field, self._clean_default)
                
                # Clean the value
                try:
                    cleaned[field] = clean_func(value)
                except Exception as e:
                    self.logger.warning(f"Error cleaning {field}: {str(e)}")
                    cleaned[field] = value
            
            # Add metadata
            cleaned['_cleaned'] = True
            cleaned['_cleaned_at'] = datetime.now().isoformat()
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning data: {str(e)}")
            return data

    def clean_batch(self, data_list: List[Dict], data_type: str) -> List[Dict]:
        """
        Clean a batch of records
        Also handles duplicate detection and removal
        """
        try:
            # Clean each record
            cleaned = [self.clean(record, data_type) for record in data_list]
            
            # Convert to dataframe for duplicate detection
            df = pd.DataFrame(cleaned)
            
            # Remove exact duplicates
            df = df.drop_duplicates()
            
            # Detect and handle similar records
            if data_type == 'property':
                df = self._handle_similar_properties(df)
            elif data_type == 'owner':
                df = self._handle_similar_owners(df)
            
            # Convert back to list of dicts
            return df.to_dict('records')
            
        except Exception as e:
            self.logger.error(f"Error cleaning batch: {str(e)}")
            return data_list

    def _clean_address(self, value: str) -> str:
        """Standardize address format"""
        if not value:
            return value
        return standardize_address(value)

    def _clean_city(self, value: str) -> str:
        """Standardize city name"""
        if not value:
            return value
        return value.strip().title()

    def _clean_state(self, value: str) -> str:
        """Standardize state code"""
        if not value:
            return value
        return value.strip().upper()

    def _clean_zipcode(self, value: Any) -> str:
        """Standardize ZIP code"""
        if not value:
            return value
        # Extract just the digits
        digits = re.sub(r'\D', '', str(value))
        # Take first 5 digits
        return digits[:5] if len(digits) >= 5 else digits

    def _clean_year(self, value: Any) -> Optional[int]:
        """Clean and validate year"""
        if not value:
            return None
        try:
            year = int(value)
            # Basic validation
            current_year = datetime.now().year
            if 1600 <= year <= current_year:
                return year
            return None
        except (ValueError, TypeError):
            return None

    def _clean_numeric(self, value: Any) -> Optional[float]:
        """Clean numeric values"""
        if not value:
            return None
        try:
            # Remove any non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', str(value))
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _clean_integer(self, value: Any) -> Optional[int]:
        """Clean integer values"""
        if not value:
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None

    def _clean_currency(self, value: Any) -> Optional[float]:
        """Clean currency values"""
        if not value:
            return None
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[^\d.-]', '', str(value))
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _clean_name(self, value: str) -> str:
        """Standardize name format"""
        if not value:
            return value
        return standardize_name(value)

    def _clean_owner_type(self, value: str) -> str:
        """Standardize owner type"""
        if not value:
            return 'unknown'
        
        value = value.lower().strip()
        
        # Map common variations
        type_map = {
            'individual': ['person', 'individual', 'single'],
            'business': ['company', 'corporation', 'llc', 'inc', 'corp'],
            'trust': ['trust', 'estate'],
            'government': ['gov', 'government', 'city', 'state', 'federal']
        }
        
        for std_type, variations in type_map.items():
            if any(v in value for v in variations):
                return std_type
        
        return 'other'

    def _clean_date(self, value: Any) -> Optional[str]:
        """Clean and standardize dates"""
        if not value:
            return None
        try:
            # Handle different date formats
            if isinstance(value, datetime):
                dt = value
            elif isinstance(value, str):
                # Try common formats
                formats = [
                    '%Y-%m-%d',
                    '%m/%d/%Y',
                    '%m-%d-%Y',
                    '%Y/%m/%d'
                ]
                for fmt in formats:
                    try:
                        dt = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return None
            else:
                return None
            
            return dt.strftime('%Y-%m-%d')
            
        except Exception:
            return None

    def _clean_default(self, value: Any) -> Any:
        """Default cleaning for unknown fields"""
        if isinstance(value, str):
            return value.strip()
        return value

    def _handle_similar_properties(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle similar property records"""
        try:
            if len(df) <= 1:
                return df
            
            # Create similarity groups
            df['address_clean'] = df['address'].fillna('').apply(
                lambda x: re.sub(r'\s+', '', x.lower())
            )
            
            # Group by similar addresses
            groups = df.groupby('address_clean')
            
            # Merge similar records
            merged = []
            for _, group in groups:
                if len(group) > 1:
                    # Merge records, keeping most recent/complete data
                    merged_record = self._merge_property_records(group)
                    merged.append(merged_record)
                else:
                    merged.append(group.iloc[0])
            
            return pd.DataFrame(merged)
            
        except Exception as e:
            self.logger.error(f"Error handling similar properties: {str(e)}")
            return df

    def _handle_similar_owners(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle similar owner records"""
        try:
            if len(df) <= 1:
                return df
            
            # Create similarity groups
            df['name_clean'] = df['name'].fillna('').apply(
                lambda x: re.sub(r'\s+', '', x.lower())
            )
            
            # Group by similar names
            groups = df.groupby('name_clean')
            
            # Merge similar records
            merged = []
            for _, group in groups:
                if len(group) > 1:
                    # Merge records, keeping most recent/complete data
                    merged_record = self._merge_owner_records(group)
                    merged.append(merged_record)
                else:
                    merged.append(group.iloc[0])
            
            return pd.DataFrame(merged)
            
        except Exception as e:
            self.logger.error(f"Error handling similar owners: {str(e)}")
            return df

    def _merge_property_records(self, group: pd.DataFrame) -> Dict:
        """Merge similar property records"""
        try:
            # Start with most recent record
            if 'updated_at' in group.columns:
                base = group.sort_values('updated_at', ascending=False).iloc[0]
            else:
                base = group.iloc[0]
            
            # Convert to dictionary
            merged = base.to_dict()
            
            # Merge numeric fields by taking most recent non-null value
            numeric_fields = [
                'square_feet', 'lot_size', 'bedrooms', 'bathrooms',
                'land_value', 'building_value', 'total_value'
            ]
            
            for field in numeric_fields:
                if field in group.columns:
                    non_null = group[field].dropna()
                    if len(non_null) > 0:
                        merged[field] = non_null.iloc[0]
            
            return merged
            
        except Exception as e:
            self.logger.error(f"Error merging property records: {str(e)}")
            return group.iloc[0].to_dict()

    def _merge_owner_records(self, group: pd.DataFrame) -> Dict:
        """Merge similar owner records"""
        try:
            # Start with most recent record
            if 'updated_at' in group.columns:
                base = group.sort_values('updated_at', ascending=False).iloc[0]
            else:
                base = group.iloc[0]
            
            # Convert to dictionary
            merged = base.to_dict()
            
            # Merge contact information by taking most recent non-null value
            contact_fields = ['phone', 'email', 'mailing_address']
            
            for field in contact_fields:
                if field in group.columns:
                    non_null = group[field].dropna()
                    if len(non_null) > 0:
                        merged[field] = non_null.iloc[0]
            
            return merged
            
        except Exception as e:
            self.logger.error(f"Error merging owner records: {str(e)}")
            return group.iloc[0].to_dict()
