"""
Data merger for combining and linking data from different sources
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from ..utils.address_matcher import AddressMatcher
from ..utils.name_matcher import NameMatcher
from ..models.property_models import Property, Owner, Transaction, Permit, Violation, UtilityRecord

class DataMerger:
    """
    Merges data from different sources and creates relationships
    Handles:
    1. Property record merging
    2. Owner linking
    3. Transaction history
    4. Permit and violation correlation
    5. Utility data integration
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Initialize matchers
        self.address_matcher = AddressMatcher()
        self.name_matcher = NameMatcher()
        
        # Configure merge thresholds
        self.thresholds = {
            'address_similarity': 0.85,  # Min similarity for address matching
            'name_similarity': 0.80,     # Min similarity for name matching
            'time_window': 90,           # Days to consider for temporal relationships
            'distance_threshold': 0.1    # Miles for spatial relationships
        }
        
        # Update thresholds from config
        if 'merge_thresholds' in config:
            self.thresholds.update(config['merge_thresholds'])

    def merge_property_data(self, 
                          assessment_data: List[Dict],
                          transaction_data: List[Dict],
                          permit_data: List[Dict],
                          violation_data: List[Dict],
                          utility_data: List[Dict]) -> List[Dict]:
        """
        Merge all property-related data into unified records
        """
        try:
            # Convert to dataframes for easier processing
            df_assessment = pd.DataFrame(assessment_data)
            df_transactions = pd.DataFrame(transaction_data)
            df_permits = pd.DataFrame(permit_data)
            df_violations = pd.DataFrame(violation_data)
            df_utilities = pd.DataFrame(utility_data)
            
            # Start with assessment data as base
            merged_properties = []
            
            for _, property_row in df_assessment.iterrows():
                try:
                    # Create base property record
                    property_record = self._create_base_property(property_row)
                    
                    # Find and merge related data
                    property_record = self._merge_transactions(
                        property_record, df_transactions
                    )
                    property_record = self._merge_permits(
                        property_record, df_permits
                    )
                    property_record = self._merge_violations(
                        property_record, df_violations
                    )
                    property_record = self._merge_utilities(
                        property_record, df_utilities
                    )
                    
                    # Add metadata
                    property_record['_merged'] = True
                    property_record['_merged_at'] = datetime.now().isoformat()
                    
                    merged_properties.append(property_record)
                    
                except Exception as e:
                    self.logger.error(f"Error merging property: {str(e)}")
                    continue
            
            return merged_properties
            
        except Exception as e:
            self.logger.error(f"Error in merge_property_data: {str(e)}")
            return []

    def merge_owner_data(self, 
                        primary_owners: List[Dict],
                        secondary_owners: List[Dict]) -> List[Dict]:
        """
        Merge and deduplicate owner records
        Links related owners and business entities
        """
        try:
            # Convert to dataframes
            df_primary = pd.DataFrame(primary_owners)
            df_secondary = pd.DataFrame(secondary_owners)
            
            # Create similarity matrix
            similarities = self._create_owner_similarity_matrix(
                df_primary, df_secondary
            )
            
            # Merge similar owners
            merged_owners = []
            processed_indices = set()
            
            for i, primary_row in df_primary.iterrows():
                if i in processed_indices:
                    continue
                    
                # Find similar owners
                similar_mask = similarities[i] >= self.thresholds['name_similarity']
                similar_indices = similar_mask[similar_mask].index
                
                if len(similar_indices) > 0:
                    # Merge all similar owners
                    owner_group = pd.concat([
                        df_primary.iloc[[i]],
                        df_secondary.iloc[similar_indices]
                    ])
                    merged_owner = self._merge_owner_group(owner_group)
                    merged_owners.append(merged_owner)
                    
                    # Mark as processed
                    processed_indices.add(i)
                    processed_indices.update(similar_indices)
                else:
                    # No similar owners found, keep original
                    merged_owners.append(primary_row.to_dict())
            
            # Add any unprocessed secondary owners
            remaining_secondary = df_secondary.index.difference(processed_indices)
            for i in remaining_secondary:
                merged_owners.append(df_secondary.iloc[i].to_dict())
            
            return merged_owners
            
        except Exception as e:
            self.logger.error(f"Error in merge_owner_data: {str(e)}")
            return []

    def merge_transaction_chains(self, transactions: List[Dict]) -> List[Dict]:
        """
        Create transaction chains and link related transactions
        """
        try:
            df = pd.DataFrame(transactions)
            
            # Sort by date
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Group by property
            chains = []
            for property_id, group in df.groupby('property_id'):
                chain = {
                    'property_id': property_id,
                    'transactions': group.to_dict('records'),
                    'summary': {
                        'total_transactions': len(group),
                        'price_history': group['price'].tolist(),
                        'ownership_duration': self._calculate_ownership_durations(group),
                        'price_trends': self._calculate_price_trends(group)
                    }
                }
                chains.append(chain)
            
            return chains
            
        except Exception as e:
            self.logger.error(f"Error in merge_transaction_chains: {str(e)}")
            return []

    def _create_base_property(self, assessment_data: pd.Series) -> Dict:
        """Create base property record from assessment data"""
        return {
            'property_id': assessment_data.get('property_id'),
            'parcel_id': assessment_data.get('parcel_id'),
            'address': assessment_data.get('address'),
            'city': assessment_data.get('city'),
            'state': assessment_data.get('state'),
            'zipcode': assessment_data.get('zipcode'),
            'property_type': assessment_data.get('property_type'),
            'year_built': assessment_data.get('year_built'),
            'square_feet': assessment_data.get('square_feet'),
            'lot_size': assessment_data.get('lot_size'),
            'bedrooms': assessment_data.get('bedrooms'),
            'bathrooms': assessment_data.get('bathrooms'),
            'assessment': {
                'land_value': assessment_data.get('land_value'),
                'building_value': assessment_data.get('building_value'),
                'total_value': assessment_data.get('total_value'),
                'assessment_year': assessment_data.get('assessment_year')
            },
            'coordinates': {
                'latitude': assessment_data.get('latitude'),
                'longitude': assessment_data.get('longitude')
            }
        }

    def _merge_transactions(self, property_record: Dict, df_transactions: pd.DataFrame) -> Dict:
        """Merge transaction data into property record"""
        try:
            # Find related transactions
            property_transactions = df_transactions[
                df_transactions['property_id'] == property_record['property_id']
            ]
            
            if len(property_transactions) > 0:
                # Sort by date
                property_transactions['date'] = pd.to_datetime(
                    property_transactions['date']
                )
                property_transactions = property_transactions.sort_values('date')
                
                # Add transaction history
                property_record['transactions'] = property_transactions.to_dict('records')
                
                # Add transaction summary
                property_record['transaction_summary'] = {
                    'total_transactions': len(property_transactions),
                    'last_sale_date': property_transactions['date'].max().isoformat(),
                    'last_sale_price': float(
                        property_transactions.iloc[-1]['price']
                    ),
                    'price_history': property_transactions['price'].tolist()
                }
            else:
                property_record['transactions'] = []
                property_record['transaction_summary'] = {
                    'total_transactions': 0
                }
            
            return property_record
            
        except Exception as e:
            self.logger.error(f"Error merging transactions: {str(e)}")
            return property_record

    def _merge_permits(self, property_record: Dict, df_permits: pd.DataFrame) -> Dict:
        """Merge permit data into property record"""
        try:
            # Find related permits
            property_permits = df_permits[
                df_permits['property_id'] == property_record['property_id']
            ]
            
            if len(property_permits) > 0:
                # Sort by date
                property_permits['issue_date'] = pd.to_datetime(
                    property_permits['issue_date']
                )
                property_permits = property_permits.sort_values('issue_date')
                
                # Add permit history
                property_record['permits'] = property_permits.to_dict('records')
                
                # Add permit summary
                property_record['permit_summary'] = {
                    'total_permits': len(property_permits),
                    'active_permits': len(
                        property_permits[property_permits['status'] == 'in_progress']
                    ),
                    'total_value': float(
                        property_permits['estimated_cost'].sum()
                    ),
                    'permit_types': property_permits['permit_type'].unique().tolist()
                }
            else:
                property_record['permits'] = []
                property_record['permit_summary'] = {
                    'total_permits': 0
                }
            
            return property_record
            
        except Exception as e:
            self.logger.error(f"Error merging permits: {str(e)}")
            return property_record

    def _merge_violations(self, property_record: Dict, df_violations: pd.DataFrame) -> Dict:
        """Merge violation data into property record"""
        try:
            # Find related violations
            property_violations = df_violations[
                df_violations['property_id'] == property_record['property_id']
            ]
            
            if len(property_violations) > 0:
                # Sort by date
                property_violations['reported_date'] = pd.to_datetime(
                    property_violations['reported_date']
                )
                property_violations = property_violations.sort_values('reported_date')
                
                # Add violation history
                property_record['violations'] = property_violations.to_dict('records')
                
                # Add violation summary
                property_record['violation_summary'] = {
                    'total_violations': len(property_violations),
                    'open_violations': len(
                        property_violations[property_violations['status'] == 'open']
                    ),
                    'total_fines': float(
                        property_violations['fines'].sum()
                    ),
                    'violation_types': property_violations['violation_type'].unique().tolist(),
                    'severity_counts': property_violations['severity'].value_counts().to_dict()
                }
            else:
                property_record['violations'] = []
                property_record['violation_summary'] = {
                    'total_violations': 0
                }
            
            return property_record
            
        except Exception as e:
            self.logger.error(f"Error merging violations: {str(e)}")
            return property_record

    def _merge_utilities(self, property_record: Dict, df_utilities: pd.DataFrame) -> Dict:
        """Merge utility data into property record"""
        try:
            # Find related utility records
            property_utilities = df_utilities[
                df_utilities['property_id'] == property_record['property_id']
            ]
            
            if len(property_utilities) > 0:
                # Group by utility type
                utility_groups = property_utilities.groupby('utility_type')
                
                # Process each utility type
                property_record['utilities'] = {}
                property_record['utility_summary'] = {
                    'total_records': len(property_utilities)
                }
                
                for utility_type, group in utility_groups:
                    # Sort by date
                    group['reading_date'] = pd.to_datetime(group['reading_date'])
                    group = group.sort_values('reading_date')
                    
                    # Calculate usage statistics
                    usage_stats = {
                        'total_usage': float(group['usage'].sum()),
                        'average_usage': float(group['usage'].mean()),
                        'max_usage': float(group['usage'].max()),
                        'min_usage': float(group['usage'].min()),
                        'last_reading': group.iloc[-1].to_dict()
                    }
                    
                    # Add to property record
                    property_record['utilities'][utility_type] = {
                        'records': group.to_dict('records'),
                        'statistics': usage_stats
                    }
            else:
                property_record['utilities'] = {}
                property_record['utility_summary'] = {
                    'total_records': 0
                }
            
            return property_record
            
        except Exception as e:
            self.logger.error(f"Error merging utilities: {str(e)}")
            return property_record

    def _create_owner_similarity_matrix(self, df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """Create similarity matrix between owner records"""
        try:
            similarities = pd.DataFrame(
                index=df1.index,
                columns=df2.index,
                dtype=float
            )
            
            for i in df1.index:
                for j in df2.index:
                    similarity = self.name_matcher.similarity(
                        df1.loc[i, 'name'],
                        df2.loc[j, 'name']
                    )
                    similarities.loc[i, j] = similarity
            
            return similarities
            
        except Exception as e:
            self.logger.error(f"Error creating similarity matrix: {str(e)}")
            return pd.DataFrame()

    def _merge_owner_group(self, group: pd.DataFrame) -> Dict:
        """Merge a group of similar owner records"""
        try:
            # Start with most recent record
            if 'updated_at' in group.columns:
                base = group.sort_values('updated_at', ascending=False).iloc[0]
            else:
                base = group.iloc[0]
            
            merged = base.to_dict()
            
            # Merge contact information
            contact_fields = ['phone', 'email', 'mailing_address']
            for field in contact_fields:
                if field in group.columns:
                    values = group[field].dropna().unique()
                    if len(values) > 0:
                        merged[field] = values[0]
            
            # Merge property relationships
            if 'properties' in group.columns:
                properties = set()
                for props in group['properties'].dropna():
                    if isinstance(props, list):
                        properties.update(props)
                merged['properties'] = list(properties)
            
            return merged
            
        except Exception as e:
            self.logger.error(f"Error merging owner group: {str(e)}")
            return group.iloc[0].to_dict()

    def _calculate_ownership_durations(self, transactions: pd.DataFrame) -> List[Dict]:
        """Calculate ownership duration for each period"""
        try:
            durations = []
            for i in range(len(transactions) - 1):
                duration = {
                    'owner': transactions.iloc[i]['buyer'],
                    'start_date': transactions.iloc[i]['date'].isoformat(),
                    'end_date': transactions.iloc[i + 1]['date'].isoformat(),
                    'days': (transactions.iloc[i + 1]['date'] - 
                            transactions.iloc[i]['date']).days
                }
                durations.append(duration)
            
            # Add current owner
            if len(transactions) > 0:
                current_duration = {
                    'owner': transactions.iloc[-1]['buyer'],
                    'start_date': transactions.iloc[-1]['date'].isoformat(),
                    'end_date': None,
                    'days': (datetime.now() - 
                            transactions.iloc[-1]['date']).days
                }
                durations.append(current_duration)
            
            return durations
            
        except Exception as e:
            self.logger.error(f"Error calculating ownership durations: {str(e)}")
            return []

    def _calculate_price_trends(self, transactions: pd.DataFrame) -> Dict:
        """Calculate price trends from transaction history"""
        try:
            if len(transactions) < 2:
                return {}
            
            # Calculate price changes
            transactions = transactions.sort_values('date')
            price_changes = []
            
            for i in range(len(transactions) - 1):
                change = {
                    'from_date': transactions.iloc[i]['date'].isoformat(),
                    'to_date': transactions.iloc[i + 1]['date'].isoformat(),
                    'from_price': float(transactions.iloc[i]['price']),
                    'to_price': float(transactions.iloc[i + 1]['price']),
                    'change': float(
                        transactions.iloc[i + 1]['price'] - 
                        transactions.iloc[i]['price']
                    ),
                    'change_percent': float(
                        (transactions.iloc[i + 1]['price'] - 
                         transactions.iloc[i]['price']) / 
                        transactions.iloc[i]['price'] * 100
                    )
                }
                price_changes.append(change)
            
            # Calculate overall trend
            total_change = float(
                transactions.iloc[-1]['price'] - 
                transactions.iloc[0]['price']
            )
            total_change_percent = float(
                (transactions.iloc[-1]['price'] - 
                 transactions.iloc[0]['price']) / 
                transactions.iloc[0]['price'] * 100
            )
            
            return {
                'price_changes': price_changes,
                'total_change': total_change,
                'total_change_percent': total_change_percent,
                'average_change_percent': float(
                    np.mean([c['change_percent'] for c in price_changes])
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating price trends: {str(e)}")
            return {}
