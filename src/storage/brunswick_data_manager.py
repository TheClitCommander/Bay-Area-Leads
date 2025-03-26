"""
Advanced data management capabilities for Brunswick data
"""
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import csv
import xlsxwriter
from .brunswick_data_store import BrunswickDataStore, CleaningResult

class BrunswickDataManager:
    def __init__(self, store: BrunswickDataStore):
        self.store = store
        self.logger = logging.getLogger(__name__)
        self.export_dir = Path("exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
    async def batch_process(
        self,
        items: List[Dict],
        item_type: str,
        batch_size: int = 100,
        max_workers: int = 4
    ) -> List[CleaningResult]:
        """Process items in batches using ThreadPoolExecutor"""
        results = []
        
        # Split items into batches
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
        
        async def process_batch(batch: List[Dict]) -> List[CleaningResult]:
            batch_results = []
            store_method = getattr(self.store, f"store_{item_type}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Process items in parallel
                futures = [
                    executor.submit(store_method, item)
                    for item in batch
                ]
                
                for future in futures:
                    try:
                        _, cleaning_result = future.result()
                        batch_results.append(cleaning_result)
                    except Exception as e:
                        self.logger.error(f"Error processing item: {e}")
                        
            return batch_results
            
        # Process all batches
        for batch in batches:
            batch_results = await process_batch(batch)
            results.extend(batch_results)
            
        return results
        
    def transform_data(self, data: Dict, transforms: List[str]) -> Dict:
        """Apply multiple data transformations"""
        transformed = data.copy()
        
        for transform in transforms:
            if transform == "merge_addresses":
                transformed = self._merge_address_components(transformed)
            elif transform == "calculate_metrics":
                transformed = self._calculate_business_metrics(transformed)
            elif transform == "enrich_location":
                transformed = self._enrich_location_data(transformed)
            elif transform == "standardize_categories":
                transformed = self._standardize_business_categories(transformed)
            elif transform == "extract_features":
                transformed = self._extract_text_features(transformed)
                
        return transformed
        
    def export_data(
        self,
        query_results: List[Dict],
        format: str = "csv",
        filename: Optional[str] = None
    ) -> str:
        """Export data to various formats"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"brunswick_data_export_{timestamp}"
            
        filepath = self.export_dir / f"{filename}.{format}"
        
        if format == "csv":
            self._export_to_csv(query_results, filepath)
        elif format == "excel":
            self._export_to_excel(query_results, filepath)
        elif format == "json":
            self._export_to_json(query_results, filepath)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
        return str(filepath)
        
    def search(
        self,
        query: Dict[str, Any],
        item_type: str,
        limit: Optional[int] = None,
        offset: int = 0,
        sort_by: Optional[str] = None,
        sort_order: str = "ASC"
    ) -> List[Dict]:
        """Search data with advanced filtering"""
        with self.store.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query
            base_query = f"SELECT * FROM {item_type}"
            where_clauses = []
            params = []
            
            for field, value in query.items():
                if isinstance(value, dict):
                    # Handle operators (e.g., {"gt": 100})
                    for op, op_value in value.items():
                        where_clause = self._build_operator_clause(field, op, op_value)
                        where_clauses.append(where_clause)
                        params.append(op_value)
                else:
                    # Simple equality
                    where_clauses.append(f"{field} = ?")
                    params.append(value)
                    
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
                
            # Add sorting
            if sort_by:
                base_query += f" ORDER BY {sort_by} {sort_order}"
                
            # Add limit and offset
            if limit is not None:
                base_query += f" LIMIT {limit} OFFSET {offset}"
                
            # Execute query
            cursor.execute(base_query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            return results
            
    def _merge_address_components(self, data: Dict) -> Dict:
        """Merge split address components"""
        if all(k in data for k in ['street_number', 'street_name', 'street_type']):
            data['full_address'] = (
                f"{data['street_number']} {data['street_name']} "
                f"{data['street_type']}"
            ).title()
        return data
        
    def _calculate_business_metrics(self, data: Dict) -> Dict:
        """Calculate business-related metrics"""
        # Add age if founding date exists
        if founding_date := data.get('founding_date'):
            try:
                founded = pd.to_datetime(founding_date)
                data['business_age'] = (
                    datetime.now() - founded
                ).days / 365.25
            except ValueError:
                pass
                
        # Calculate permit activity score
        if permits := data.get('permits', []):
            data['permit_activity_score'] = len(permits)
            
        return data
        
    def _enrich_location_data(self, data: Dict) -> Dict:
        """Add location-based enrichments"""
        if address := data.get('normalized_address'):
            # Add Brunswick neighborhood
            data['neighborhood'] = self._get_neighborhood(address)
            
            # Add business district info
            data['business_district'] = self._get_business_district(address)
            
            # Add zoning info if not present
            if 'zoning' not in data:
                data['zoning'] = self._get_zoning(address)
                
        return data
        
    def _standardize_business_categories(self, data: Dict) -> Dict:
        """Standardize business categories"""
        if category := data.get('category'):
            # Map to standard categories
            category_map = {
                'RESTAURANT': ['RESTAURANT', 'DINING', 'CAFE', 'EATERY'],
                'RETAIL': ['RETAIL', 'SHOP', 'STORE'],
                'PROFESSIONAL': ['OFFICE', 'CONSULTING', 'PROFESSIONAL'],
                'SERVICE': ['SERVICE', 'REPAIR', 'MAINTENANCE']
            }
            
            category = category.upper()
            for std_category, variants in category_map.items():
                if any(variant in category for variant in variants):
                    data['standardized_category'] = std_category
                    break
                    
        return data
        
    def _extract_text_features(self, data: Dict) -> Dict:
        """Extract features from text fields"""
        # Extract business name features
        if name := data.get('name'):
            data['name_features'] = {
                'words': len(name.split()),
                'has_location': 'BRUNSWICK' in name.upper(),
                'has_service': any(
                    service in name.upper()
                    for service in ['SERVICE', 'REPAIR', 'CONSULTING']
                )
            }
            
        # Extract description features
        if description := data.get('description'):
            data['description_features'] = {
                'length': len(description),
                'sentence_count': description.count('.'),
                'has_contact': any(
                    contact in description.lower()
                    for contact in ['call', 'email', 'contact']
                )
            }
            
        return data
        
    def _export_to_csv(self, data: List[Dict], filepath: Path):
        """Export data to CSV"""
        if not data:
            return
            
        # Flatten nested dictionaries
        flat_data = []
        for item in data:
            flat_item = {}
            for key, value in item.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        flat_item[f"{key}_{sub_key}"] = sub_value
                else:
                    flat_item[key] = value
            flat_data.append(flat_item)
            
        # Write to CSV
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=flat_data[0].keys())
            writer.writeheader()
            writer.writerows(flat_data)
            
    def _export_to_excel(self, data: List[Dict], filepath: Path):
        """Export data to Excel with formatting"""
        workbook = xlsxwriter.Workbook(str(filepath))
        worksheet = workbook.add_worksheet()
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white'
        })
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        
        # Write headers
        headers = list(data[0].keys())
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            
        # Write data
        for row, item in enumerate(data, start=1):
            for col, header in enumerate(headers):
                value = item[header]
                if isinstance(value, datetime):
                    worksheet.write(row, col, value, date_format)
                else:
                    worksheet.write(row, col, value)
                    
        # Auto-adjust column widths
        for col, header in enumerate(headers):
            worksheet.set_column(col, col, len(header) + 2)
            
        workbook.close()
        
    def _export_to_json(self, data: List[Dict], filepath: Path):
        """Export data to JSON with formatting"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            
    def _build_operator_clause(
        self,
        field: str,
        operator: str,
        value: Any
    ) -> str:
        """Build SQL where clause for operators"""
        op_map = {
            'eq': '=',
            'neq': '!=',
            'gt': '>',
            'gte': '>=',
            'lt': '<',
            'lte': '<=',
            'like': 'LIKE',
            'in': 'IN',
            'between': 'BETWEEN'
        }
        
        if operator not in op_map:
            raise ValueError(f"Unsupported operator: {operator}")
            
        return f"{field} {op_map[operator]} ?"
        
    def _get_neighborhood(self, address: str) -> Optional[str]:
        """Get Brunswick neighborhood for address"""
        # This would typically use GIS data
        # Simplified example
        neighborhoods = {
            'MAINE ST': 'Downtown',
            'FEDERAL ST': 'Downtown',
            'BATH RD': "Cook's Corner",
            'ADMIRAL FITCH': 'Brunswick Landing'
        }
        
        for street, neighborhood in neighborhoods.items():
            if street in address:
                return neighborhood
        return None
        
    def _get_business_district(self, address: str) -> Optional[str]:
        """Get business district for address"""
        # Simplified example
        districts = {
            'MAINE ST': 'Downtown District',
            'BATH RD': 'Cook\'s Corner District',
            'ADMIRAL FITCH': 'Brunswick Landing District'
        }
        
        for street, district in districts.items():
            if street in address:
                return district
        return None
        
    def _get_zoning(self, address: str) -> Optional[str]:
        """Get zoning for address"""
        # Simplified example
        zoning = {
            'MAINE ST': 'TC1 - Town Center 1',
            'BATH RD': 'HC1 - Highway Commercial',
            'ADMIRAL FITCH': 'GI - Growth Industrial'
        }
        
        for street, zone in zoning.items():
            if street in address:
                return zone
        return None
