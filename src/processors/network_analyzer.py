"""
Analyzes networks and relationships between properties, owners, and market activities
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import networkx as nx
from networkx.algorithms import community
from sklearn.cluster import DBSCAN
from fuzzywuzzy import fuzz
import json

class NetworkAnalyzer:
    """
    Analyzes networks and relationships including:
    1. Owner networks and relationships
    2. Property transaction patterns
    3. Investment group detection
    4. Geographic clustering
    5. Market activity networks
    """
    
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config or {}
        
        # Configure analysis parameters
        self.params = {
            'name_similarity_threshold': 85,  # Fuzzy matching threshold
            'transaction_window': 180,        # Days to consider related transactions
            'geographic_radius': 0.5,         # Miles for geographic clustering
            'min_relationship_strength': 2    # Minimum connections for strong relationship
        }
        
        # Update from config
        if 'network_params' in config:
            self.params.update(config['network_params'])
        
        # Initialize network storage
        self.networks = {
            'owner': nx.Graph(),
            'property': nx.Graph(),
            'transaction': nx.DiGraph(),
            'geographic': nx.Graph(),
            'market': nx.Graph()
        }

    def analyze_owner_networks(self, properties: List[Dict]) -> Dict:
        """
        Analyze networks between property owners
        """
        try:
            # Build owner network
            G = nx.Graph()
            
            # Extract all owners and properties
            owner_properties = {}
            for prop in properties:
                transactions = prop.get('transactions', [])
                for trans in transactions:
                    owner = trans.get('buyer')
                    if owner:
                        if owner not in owner_properties:
                            owner_properties[owner] = []
                        owner_properties[owner].append(prop['property_id'])
            
            # Add nodes for owners
            for owner in owner_properties:
                G.add_node(
                    owner,
                    type='owner',
                    properties=owner_properties[owner],
                    property_count=len(owner_properties[owner])
                )
            
            # Connect related owners
            self._connect_related_owners(G, owner_properties)
            
            # Find communities
            communities = self._detect_owner_communities(G)
            
            # Analyze investment patterns
            patterns = self._analyze_investment_patterns(G, properties)
            
            # Store network
            self.networks['owner'] = G
            
            return {
                'network_stats': self._calculate_network_stats(G),
                'communities': communities,
                'patterns': patterns,
                'key_players': self._identify_key_players(G),
                'relationships': self._extract_relationships(G)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing owner networks: {str(e)}")
            return {}

    def analyze_transaction_patterns(self, properties: List[Dict]) -> Dict:
        """
        Analyze property transaction patterns
        """
        try:
            # Build transaction network
            G = nx.DiGraph()
            
            # Add nodes and edges for transactions
            for prop in properties:
                transactions = prop.get('transactions', [])
                for i in range(len(transactions) - 1):
                    current = transactions[i]
                    next_trans = transactions[i + 1]
                    
                    # Add transaction nodes
                    G.add_node(
                        f"T{current['transaction_id']}",
                        type='transaction',
                        property_id=prop['property_id'],
                        date=current['date'],
                        price=current['price'],
                        buyer=current['buyer'],
                        seller=current['seller']
                    )
                    
                    # Add directed edge between transactions
                    G.add_edge(
                        f"T{current['transaction_id']}",
                        f"T{next_trans['transaction_id']}",
                        time_delta=(
                            datetime.fromisoformat(next_trans['date']) -
                            datetime.fromisoformat(current['date'])
                        ).days,
                        price_change=next_trans['price'] - current['price'],
                        price_change_pct=(
                            (next_trans['price'] - current['price']) /
                            current['price'] * 100
                        )
                    )
            
            # Store network
            self.networks['transaction'] = G
            
            # Analyze patterns
            patterns = {
                'network_stats': self._calculate_network_stats(G),
                'transaction_chains': self._identify_transaction_chains(G),
                'price_patterns': self._analyze_price_patterns(G),
                'temporal_patterns': self._analyze_temporal_patterns(G),
                'buyer_seller_patterns': self._analyze_buyer_seller_patterns(G)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing transaction patterns: {str(e)}")
            return {}

    def detect_investment_groups(self, properties: List[Dict]) -> List[Dict]:
        """
        Detect and analyze investment groups
        """
        try:
            groups = []
            
            # Get owner network
            G = self.networks.get('owner')
            if not G:
                G = self.analyze_owner_networks(properties)['network']
            
            # Detect communities
            communities = list(community.greedy_modularity_communities(G))
            
            # Analyze each community
            for i, comm in enumerate(communities):
                try:
                    # Get subgraph for community
                    subgraph = G.subgraph(comm)
                    
                    # Calculate group metrics
                    metrics = self._calculate_group_metrics(subgraph, properties)
                    
                    # Identify key members
                    key_members = self._identify_key_members(subgraph)
                    
                    # Analyze investment strategy
                    strategy = self._analyze_investment_strategy(
                        subgraph,
                        properties
                    )
                    
                    groups.append({
                        'group_id': f"G{i}",
                        'members': list(comm),
                        'size': len(comm),
                        'metrics': metrics,
                        'key_members': key_members,
                        'strategy': strategy,
                        'properties': self._get_group_properties(comm, properties)
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error analyzing group: {str(e)}")
                    continue
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Error detecting investment groups: {str(e)}")
            return []

    def analyze_geographic_clusters(self, properties: List[Dict]) -> Dict:
        """
        Analyze geographic clustering of properties
        """
        try:
            # Build geographic network
            G = nx.Graph()
            
            # Add property nodes
            for prop in properties:
                coords = prop.get('coordinates', {})
                if coords.get('latitude') and coords.get('longitude'):
                    G.add_node(
                        prop['property_id'],
                        type='property',
                        latitude=coords['latitude'],
                        longitude=coords['longitude'],
                        property_type=prop.get('property_type'),
                        value=prop.get('assessment', {}).get('total_value')
                    )
            
            # Connect nearby properties
            self._connect_nearby_properties(G)
            
            # Store network
            self.networks['geographic'] = G
            
            # Analyze clusters
            clusters = self._analyze_geographic_clusters(G)
            
            return {
                'network_stats': self._calculate_network_stats(G),
                'clusters': clusters,
                'hotspots': self._identify_hotspots(G),
                'patterns': self._analyze_spatial_patterns(G)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing geographic clusters: {str(e)}")
            return {}

    def analyze_market_activity(self, properties: List[Dict]) -> Dict:
        """
        Analyze networks in market activity
        """
        try:
            # Build market activity network
            G = nx.Graph()
            
            # Add nodes for different market activities
            self._add_market_activity_nodes(G, properties)
            
            # Connect related activities
            self._connect_market_activities(G)
            
            # Store network
            self.networks['market'] = G
            
            # Analyze patterns
            patterns = {
                'network_stats': self._calculate_network_stats(G),
                'activity_clusters': self._analyze_activity_clusters(G),
                'temporal_patterns': self._analyze_activity_timing(G),
                'relationship_patterns': self._analyze_activity_relationships(G)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing market activity: {str(e)}")
            return {}

    def _connect_related_owners(self, G: nx.Graph, owner_properties: Dict) -> None:
        """Connect owners based on various relationships"""
        try:
            # Connect by similar names
            owners = list(owner_properties.keys())
            for i in range(len(owners)):
                for j in range(i + 1, len(owners)):
                    if fuzz.ratio(owners[i], owners[j]) >= self.params['name_similarity_threshold']:
                        G.add_edge(
                            owners[i],
                            owners[j],
                            relationship_type='similar_name',
                            strength=fuzz.ratio(owners[i], owners[j]) / 100
                        )
            
            # Connect by shared properties
            for i in range(len(owners)):
                for j in range(i + 1, len(owners)):
                    shared = set(owner_properties[owners[i]]) & set(owner_properties[owners[j]])
                    if shared:
                        G.add_edge(
                            owners[i],
                            owners[j],
                            relationship_type='shared_property',
                            shared_properties=list(shared),
                            strength=len(shared)
                        )
            
        except Exception as e:
            self.logger.error(f"Error connecting related owners: {str(e)}")

    def _detect_owner_communities(self, G: nx.Graph) -> List[Dict]:
        """Detect and analyze owner communities"""
        try:
            communities = []
            
            # Detect communities using Louvain method
            partition = community.louvain_communities(G)
            
            # Analyze each community
            for i, nodes in enumerate(partition):
                comm = {
                    'community_id': f"C{i}",
                    'size': len(nodes),
                    'members': list(nodes),
                    'total_properties': sum(
                        G.nodes[node]['property_count']
                        for node in nodes
                    ),
                    'density': nx.density(G.subgraph(nodes)),
                    'key_members': [
                        node for node in nodes
                        if G.degree[node] >= self.params['min_relationship_strength']
                    ]
                }
                communities.append(comm)
            
            return communities
            
        except Exception as e:
            self.logger.error(f"Error detecting owner communities: {str(e)}")
            return []

    def _analyze_investment_patterns(self, G: nx.Graph, properties: List[Dict]) -> Dict:
        """Analyze investment patterns within the network"""
        try:
            patterns = {
                'transaction_patterns': self._analyze_transaction_timing(G, properties),
                'property_type_patterns': self._analyze_property_preferences(G, properties),
                'geographic_patterns': self._analyze_geographic_preferences(G, properties),
                'value_patterns': self._analyze_value_preferences(G, properties)
            }
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error analyzing investment patterns: {str(e)}")
            return {}

    def _identify_key_players(self, G: nx.Graph) -> List[Dict]:
        """Identify key players in the network"""
        try:
            key_players = []
            
            # Calculate centrality metrics
            degree_cent = nx.degree_centrality(G)
            between_cent = nx.betweenness_centrality(G)
            eigen_cent = nx.eigenvector_centrality(G)
            
            # Identify key players
            for node in G.nodes():
                if G.nodes[node]['type'] == 'owner':
                    importance = (
                        degree_cent[node] +
                        between_cent[node] +
                        eigen_cent[node]
                    ) / 3
                    
                    if importance > 0.1:  # Threshold for key players
                        key_players.append({
                            'id': node,
                            'importance_score': float(importance),
                            'property_count': G.nodes[node]['property_count'],
                            'connections': list(G.neighbors(node)),
                            'centrality': {
                                'degree': float(degree_cent[node]),
                                'betweenness': float(between_cent[node]),
                                'eigenvector': float(eigen_cent[node])
                            }
                        })
            
            # Sort by importance
            key_players.sort(key=lambda x: x['importance_score'], reverse=True)
            
            return key_players
            
        except Exception as e:
            self.logger.error(f"Error identifying key players: {str(e)}")
            return []

    def _calculate_group_metrics(self, G: nx.Graph, properties: List[Dict]) -> Dict:
        """Calculate metrics for an investment group"""
        try:
            metrics = {
                'network_metrics': {
                    'density': nx.density(G),
                    'avg_clustering': nx.average_clustering(G),
                    'diameter': nx.diameter(G)
                },
                'investment_metrics': self._calculate_investment_metrics(G, properties),
                'activity_metrics': self._calculate_activity_metrics(G, properties),
                'temporal_metrics': self._calculate_temporal_metrics(G, properties)
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating group metrics: {str(e)}")
            return {}

    def _analyze_investment_strategy(self, G: nx.Graph, properties: List[Dict]) -> Dict:
        """Analyze investment strategy of a group"""
        try:
            strategy = {
                'property_preferences': self._analyze_property_preferences(G, properties),
                'transaction_patterns': self._analyze_transaction_patterns(G, properties),
                'geographic_focus': self._analyze_geographic_focus(G, properties),
                'value_strategy': self._analyze_value_strategy(G, properties),
                'timing_patterns': self._analyze_timing_patterns(G, properties)
            }
            
            return strategy
            
        except Exception as e:
            self.logger.error(f"Error analyzing investment strategy: {str(e)}")
            return {}
