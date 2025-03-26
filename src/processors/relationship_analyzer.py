"""
Analyzes relationships between properties, owners, and market activities
"""
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from geopy.distance import geodesic

class RelationshipAnalyzer:
    """
    Analyzes and discovers relationships in property data
    Handles:
    1. Geographic clustering
    2. Owner networks
    3. Market activity patterns
    4. Property comparisons
    5. Investment patterns
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Configure analysis parameters
        self.params = {
            'geo_cluster_radius': 0.5,  # Miles
            'time_window': 180,         # Days
            'min_similarity': 0.7,      # For property comparison
            'min_cluster_size': 3       # For pattern detection
        }
        
        # Update from config
        if 'analysis_params' in config:
            self.params.update(config['analysis_params'])

    def analyze_geographic_clusters(self, properties: List[Dict]) -> List[Dict]:
        """
        Find geographic clusters of properties
        Useful for identifying neighborhood patterns
        """
        try:
            # Extract coordinates
            coords = []
            valid_properties = []
            
            for prop in properties:
                lat = prop.get('coordinates', {}).get('latitude')
                lng = prop.get('coordinates', {}).get('longitude')
                
                if lat is not None and lng is not None:
                    coords.append([lat, lng])
                    valid_properties.append(prop)
            
            if not coords:
                return []
            
            # Convert to numpy array
            X = np.array(coords)
            
            # Convert radius to degrees (approximate)
            radius_degrees = self.params['geo_cluster_radius'] / 69.0  # miles to degrees
            
            # Run DBSCAN clustering
            clustering = DBSCAN(
                eps=radius_degrees,
                min_samples=self.params['min_cluster_size'],
                metric='euclidean'
            ).fit(X)
            
            # Process clusters
            clusters = []
            for cluster_id in set(clustering.labels_):
                if cluster_id == -1:  # Noise points
                    continue
                    
                # Get properties in this cluster
                cluster_mask = clustering.labels_ == cluster_id
                cluster_properties = [
                    valid_properties[i] for i in range(len(valid_properties))
                    if cluster_mask[i]
                ]
                
                # Calculate cluster statistics
                cluster_stats = self._calculate_cluster_stats(cluster_properties)
                
                clusters.append({
                    'cluster_id': int(cluster_id),
                    'properties': cluster_properties,
                    'statistics': cluster_stats,
                    'center': {
                        'latitude': float(np.mean(X[cluster_mask, 0])),
                        'longitude': float(np.mean(X[cluster_mask, 1]))
                    }
                })
            
            return clusters
            
        except Exception as e:
            self.logger.error(f"Error in geographic clustering: {str(e)}")
            return []

    def analyze_owner_networks(self, properties: List[Dict]) -> List[Dict]:
        """
        Analyze ownership networks and patterns
        Identifies related owners and investment groups
        """
        try:
            # Build owner network
            owner_properties = {}  # owner -> properties
            property_owners = {}   # property -> owners
            
            for prop in properties:
                # Get current and historical owners
                owners = set()
                
                # Current owner
                if 'owner' in prop:
                    owners.add(prop['owner'].get('name'))
                
                # Historical owners from transactions
                for trans in prop.get('transactions', []):
                    owners.add(trans.get('buyer'))
                    owners.add(trans.get('seller'))
                
                # Remove None values
                owners = {o for o in owners if o}
                
                # Update mappings
                property_owners[prop['property_id']] = owners
                for owner in owners:
                    if owner not in owner_properties:
                        owner_properties[owner] = set()
                    owner_properties[owner].add(prop['property_id'])
            
            # Find owner networks
            networks = []
            processed_owners = set()
            
            for owner in owner_properties:
                if owner in processed_owners:
                    continue
                
                # Find related owners
                network = self._find_related_owners(
                    owner,
                    owner_properties,
                    property_owners
                )
                
                if len(network) > 1:  # Only include networks with multiple owners
                    # Get all properties in network
                    network_properties = set()
                    for network_owner in network:
                        network_properties.update(owner_properties[network_owner])
                    
                    # Calculate network statistics
                    network_stats = self._calculate_network_stats(
                        network,
                        network_properties,
                        properties
                    )
                    
                    networks.append({
                        'owners': list(network),
                        'properties': list(network_properties),
                        'statistics': network_stats
                    })
                
                processed_owners.update(network)
            
            return networks
            
        except Exception as e:
            self.logger.error(f"Error in owner network analysis: {str(e)}")
            return []

    def analyze_market_patterns(self, properties: List[Dict]) -> Dict:
        """
        Analyze market activity patterns
        Identifies trends and unusual activity
        """
        try:
            # Extract transaction data
            transactions = []
            for prop in properties:
                for trans in prop.get('transactions', []):
                    trans['property_id'] = prop['property_id']
                    trans['property_type'] = prop.get('property_type')
                    transactions.append(trans)
            
            if not transactions:
                return {}
            
            # Convert to dataframe
            df = pd.DataFrame(transactions)
            df['date'] = pd.to_datetime(df['date'])
            
            # Analyze patterns
            patterns = {
                'temporal': self._analyze_temporal_patterns(df),
                'price': self._analyze_price_patterns(df),
                'property_type': self._analyze_type_patterns(df),
                'buyer_seller': self._analyze_buyer_seller_patterns(df)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error in market pattern analysis: {str(e)}")
            return {}

    def find_similar_properties(self, 
                              target_property: Dict,
                              comparison_properties: List[Dict],
                              n_similar: int = 5) -> List[Dict]:
        """
        Find properties similar to target property
        Uses multiple criteria for comparison
        """
        try:
            similarities = []
            
            for prop in comparison_properties:
                if prop['property_id'] == target_property['property_id']:
                    continue
                
                # Calculate similarity score
                similarity = self._calculate_property_similarity(
                    target_property, prop
                )
                
                if similarity >= self.params['min_similarity']:
                    similarities.append({
                        'property': prop,
                        'similarity_score': similarity,
                        'comparison': self._compare_properties(
                            target_property, prop
                        )
                    })
            
            # Sort by similarity score
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return similarities[:n_similar]
            
        except Exception as e:
            self.logger.error(f"Error finding similar properties: {str(e)}")
            return []

    def _calculate_cluster_stats(self, properties: List[Dict]) -> Dict:
        """Calculate statistics for a property cluster"""
        try:
            # Extract numeric values
            values = pd.DataFrame([
                {
                    'total_value': p.get('assessment', {}).get('total_value'),
                    'square_feet': p.get('square_feet'),
                    'year_built': p.get('year_built')
                }
                for p in properties
            ])
            
            stats = {
                'count': len(properties),
                'avg_value': float(values['total_value'].mean()),
                'avg_sqft': float(values['square_feet'].mean()),
                'avg_year': float(values['year_built'].mean()),
                'property_types': self._count_occurrences(
                    [p.get('property_type') for p in properties]
                )
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating cluster stats: {str(e)}")
            return {}

    def _find_related_owners(self,
                           start_owner: str,
                           owner_properties: Dict[str, Set[str]],
                           property_owners: Dict[str, Set[str]]) -> Set[str]:
        """Find network of related owners through shared properties"""
        try:
            related = {start_owner}
            to_process = {start_owner}
            
            while to_process:
                owner = to_process.pop()
                
                # Get all properties owned by this owner
                properties = owner_properties[owner]
                
                # Find other owners of these properties
                for prop_id in properties:
                    for other_owner in property_owners[prop_id]:
                        if other_owner not in related:
                            related.add(other_owner)
                            to_process.add(other_owner)
            
            return related
            
        except Exception as e:
            self.logger.error(f"Error finding related owners: {str(e)}")
            return {start_owner}

    def _calculate_network_stats(self,
                               owners: Set[str],
                               property_ids: Set[str],
                               all_properties: List[Dict]) -> Dict:
        """Calculate statistics for an owner network"""
        try:
            # Get full property details
            network_properties = [
                p for p in all_properties
                if p['property_id'] in property_ids
            ]
            
            stats = {
                'owner_count': len(owners),
                'property_count': len(property_ids),
                'total_value': sum(
                    p.get('assessment', {}).get('total_value', 0)
                    for p in network_properties
                ),
                'property_types': self._count_occurrences(
                    [p.get('property_type') for p in network_properties]
                ),
                'transaction_volume': sum(
                    len(p.get('transactions', []))
                    for p in network_properties
                )
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating network stats: {str(e)}")
            return {}

    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze temporal patterns in market activity"""
        try:
            # Resample to monthly frequency
            monthly = df.set_index('date').resample('M').agg({
                'price': ['count', 'mean'],
                'property_id': 'nunique'
            })
            
            # Calculate trends
            activity_trend = np.polyfit(
                range(len(monthly)),
                monthly[('price', 'count')],
                1
            )
            
            price_trend = np.polyfit(
                range(len(monthly)),
                monthly[('price', 'mean')],
                1
            )
            
            return {
                'monthly_volume': monthly[('price', 'count')].tolist(),
                'monthly_avg_price': monthly[('price', 'mean')].tolist(),
                'unique_properties': monthly[('property_id', 'nunique')].tolist(),
                'activity_trend': float(activity_trend[0]),
                'price_trend': float(price_trend[0])
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing temporal patterns: {str(e)}")
            return {}

    def _analyze_price_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns in property prices"""
        try:
            stats = {
                'mean_price': float(df['price'].mean()),
                'median_price': float(df['price'].median()),
                'price_std': float(df['price'].std()),
                'price_range': {
                    'min': float(df['price'].min()),
                    'max': float(df['price'].max())
                }
            }
            
            # Detect price segments
            segments = pd.qcut(
                df['price'],
                4,
                labels=['low', 'medium', 'high', 'premium']
            )
            
            stats['price_segments'] = {
                label: len(segments[segments == label])
                for label in segments.unique()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing price patterns: {str(e)}")
            return {}

    def _analyze_type_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns by property type"""
        try:
            type_stats = df.groupby('property_type').agg({
                'price': ['count', 'mean', 'median'],
                'property_id': 'nunique'
            })
            
            patterns = {}
            for prop_type in type_stats.index:
                patterns[prop_type] = {
                    'transaction_count': int(
                        type_stats.loc[prop_type, ('price', 'count')]
                    ),
                    'avg_price': float(
                        type_stats.loc[prop_type, ('price', 'mean')]
                    ),
                    'median_price': float(
                        type_stats.loc[prop_type, ('price', 'median')]
                    ),
                    'unique_properties': int(
                        type_stats.loc[prop_type, ('property_id', 'nunique')]
                    )
                }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing type patterns: {str(e)}")
            return {}

    def _analyze_buyer_seller_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze patterns in buyer and seller behavior"""
        try:
            # Count transactions per buyer/seller
            buyer_counts = df['buyer'].value_counts()
            seller_counts = df['seller'].value_counts()
            
            # Identify frequent participants
            frequent_buyers = [
                {
                    'name': name,
                    'transactions': int(count)
                }
                for name, count in buyer_counts.items()
                if count > 1
            ]
            
            frequent_sellers = [
                {
                    'name': name,
                    'transactions': int(count)
                }
                for name, count in seller_counts.items()
                if count > 1
            ]
            
            return {
                'frequent_buyers': frequent_buyers,
                'frequent_sellers': frequent_sellers,
                'unique_buyers': len(buyer_counts),
                'unique_sellers': len(seller_counts)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing buyer/seller patterns: {str(e)}")
            return {}

    def _calculate_property_similarity(self,
                                    prop1: Dict,
                                    prop2: Dict) -> float:
        """Calculate similarity score between two properties"""
        try:
            scores = []
            
            # Compare numeric features
            numeric_features = [
                ('square_feet', 0.3),
                ('lot_size', 0.2),
                ('bedrooms', 0.1),
                ('bathrooms', 0.1)
            ]
            
            for feature, weight in numeric_features:
                val1 = prop1.get(feature)
                val2 = prop2.get(feature)
                
                if val1 is not None and val2 is not None:
                    similarity = 1 - min(abs(val1 - val2) / max(val1, val2), 1)
                    scores.append(similarity * weight)
            
            # Compare categorical features
            if prop1.get('property_type') == prop2.get('property_type'):
                scores.append(0.2)
            
            # Compare location
            coords1 = prop1.get('coordinates', {})
            coords2 = prop2.get('coordinates', {})
            
            if all(coords1.values()) and all(coords2.values()):
                distance = geodesic(
                    (coords1['latitude'], coords1['longitude']),
                    (coords2['latitude'], coords2['longitude'])
                ).miles
                
                # Convert distance to similarity score
                distance_score = max(
                    0,
                    1 - (distance / self.params['geo_cluster_radius'])
                )
                scores.append(distance_score * 0.1)
            
            return sum(scores) / sum(weight for _, weight in numeric_features + [(None, 0.2), (None, 0.1)])
            
        except Exception as e:
            self.logger.error(f"Error calculating property similarity: {str(e)}")
            return 0.0

    def _compare_properties(self, prop1: Dict, prop2: Dict) -> Dict:
        """Generate detailed comparison between two properties"""
        try:
            comparison = {
                'features': {},
                'location': {},
                'value': {}
            }
            
            # Compare features
            for feature in ['square_feet', 'lot_size', 'bedrooms', 'bathrooms']:
                val1 = prop1.get(feature)
                val2 = prop2.get(feature)
                
                if val1 is not None and val2 is not None:
                    difference = val2 - val1
                    percent_diff = (difference / val1) * 100 if val1 != 0 else 0
                    
                    comparison['features'][feature] = {
                        'difference': difference,
                        'percent_difference': percent_diff
                    }
            
            # Compare location
            coords1 = prop1.get('coordinates', {})
            coords2 = prop2.get('coordinates', {})
            
            if all(coords1.values()) and all(coords2.values()):
                distance = geodesic(
                    (coords1['latitude'], coords1['longitude']),
                    (coords2['latitude'], coords2['longitude'])
                ).miles
                
                comparison['location'] = {
                    'distance_miles': distance
                }
            
            # Compare value
            value1 = prop1.get('assessment', {}).get('total_value')
            value2 = prop2.get('assessment', {}).get('total_value')
            
            if value1 is not None and value2 is not None:
                value_diff = value2 - value1
                value_percent = (value_diff / value1) * 100 if value1 != 0 else 0
                
                comparison['value'] = {
                    'difference': value_diff,
                    'percent_difference': value_percent
                }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing properties: {str(e)}")
            return {}

    def _count_occurrences(self, items: List[Any]) -> Dict[str, int]:
        """Count occurrences of items in a list"""
        try:
            counts = {}
            for item in items:
                if item:
                    counts[str(item)] = counts.get(str(item), 0) + 1
            return counts
        except Exception:
            return {}
