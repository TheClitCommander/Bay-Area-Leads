"""
A clean, intuitive interface for finding and managing properties
Think of this as the 'Finder' for properties
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from ..models.property_models import Property, Owner, PropertyScore
from ..services.db_service import DatabaseService

class PropertyFinder:
    """
    Simple, elegant property finder
    Like Spotlight Search for properties
    """
    
    def __init__(self):
        self.db = DatabaseService()
        self.logger = logging.getLogger(self.__class__.__name__)

    def quick_find(self, search_text: str) -> List[Dict]:
        """
        Quick search - like Spotlight Search
        Just type anything - address, owner, price range, etc.
        """
        try:
            with self.db.session() as session:
                # Smart search that figures out what you're looking for
                if search_text.startswith("$"):
                    # Looking for properties in a price range
                    return self._find_by_price(session, search_text)
                elif any(word in search_text.lower() for word in ["bed", "bath", "sqft"]):
                    # Looking for properties by features
                    return self._find_by_features(session, search_text)
                elif "@" in search_text:
                    # Looking for properties by owner email
                    return self._find_by_owner_email(session, search_text)
                else:
                    # General search - will look everywhere
                    return self._smart_search(session, search_text)

        except Exception as e:
            self.logger.error(f"Error in quick find: {str(e)}")
            return []

    def get_property_preview(self, property_id: int) -> Dict:
        """
        Quick preview of a property
        Like Quick Look on Mac
        """
        try:
            with self.db.session() as session:
                property = session.query(Property).get(property_id)
                if not property:
                    return {}

                return {
                    "preview": {
                        "address": property.address,
                        "image": "property_image_url",  # Would be actual image
                        "value": f"${property.total_value:,}",
                        "quick_facts": {
                            "type": property.property_type,
                            "size": f"{property.square_feet:,} sqft",
                            "beds": f"{property.bedrooms} beds",
                            "baths": f"{property.bathrooms} baths"
                        }
                    },
                    "scores": {
                        "total": f"{property.scores[0].total_score:.0%}",
                        "potential": f"{property.scores[0].potential_score:.0%}",
                        "risk": f"{property.scores[0].risk_score:.0%}"
                    } if property.scores else {},
                    "actions": self._get_quick_actions(property)
                }

        except Exception as e:
            self.logger.error(f"Error getting preview: {str(e)}")
            return {}

    def get_property_details(self, property_id: int) -> Dict:
        """
        Detailed property view
        Like getting info (⌘ + I) in Finder
        """
        try:
            with self.db.session() as session:
                property = session.query(Property).get(property_id)
                if not property:
                    return {}

                return {
                    "basics": {
                        "address": property.address,
                        "type": property.property_type,
                        "year_built": property.year_built,
                        "last_updated": property.updated_at.strftime("%b %d, %Y")
                    },
                    "details": {
                        "size": f"{property.square_feet:,} sqft",
                        "lot": f"{property.lot_size:,} sqft",
                        "beds": property.bedrooms,
                        "baths": property.bathrooms,
                        "units": property.units
                    },
                    "value": {
                        "total": f"${property.total_value:,}",
                        "land": f"${property.land_value:,}",
                        "building": f"${property.building_value:,}",
                        "last_assessed": property.last_assessment_date.strftime("%b %d, %Y")
                    },
                    "owner": {
                        "name": property.owner.name,
                        "type": property.owner.owner_type,
                        "since": property.transactions[0].date.strftime("%b %d, %Y")
                            if property.transactions else "Unknown"
                    },
                    "location": {
                        "zone": property.zone_code,
                        "flood_zone": property.flood_zone,
                        "latitude": property.latitude,
                        "longitude": property.longitude
                    }
                }

        except Exception as e:
            self.logger.error(f"Error getting details: {str(e)}")
            return {}

    def get_smart_suggestions(self, property_id: int) -> Dict:
        """
        Smart suggestions based on property
        Like Siri Suggestions
        """
        try:
            with self.db.session() as session:
                property = session.query(Property).get(property_id)
                if not property:
                    return {}

                return {
                    "similar_properties": self._find_similar(session, property),
                    "suggested_actions": self._get_suggested_actions(property),
                    "insights": self._get_smart_insights(property)
                }

        except Exception as e:
            self.logger.error(f"Error getting suggestions: {str(e)}")
            return {}

    def _find_by_price(self, session: Session, price_text: str) -> List[Dict]:
        """Smart price search - handles ranges and approximates"""
        try:
            # Clean up price text: "$200k" -> 200000
            price = self._parse_price(price_text)
            
            # Find properties within 10% of target price
            margin = price * 0.1
            properties = session.query(Property).filter(
                Property.total_value.between(price - margin, price + margin)
            ).limit(10).all()

            return [self._format_quick_result(p) for p in properties]

        except Exception as e:
            self.logger.error(f"Error in price search: {str(e)}")
            return []

    def _find_by_features(self, session: Session, feature_text: str) -> List[Dict]:
        """Smart feature search - handles natural language"""
        try:
            features = self._parse_features(feature_text)
            query = session.query(Property)
            
            if "beds" in features:
                query = query.filter(Property.bedrooms == features["beds"])
            if "baths" in features:
                query = query.filter(Property.bathrooms == features["baths"])
            if "sqft" in features:
                margin = features["sqft"] * 0.1
                query = query.filter(Property.square_feet.between(
                    features["sqft"] - margin, features["sqft"] + margin
                ))

            properties = query.limit(10).all()
            return [self._format_quick_result(p) for p in properties]

        except Exception as e:
            self.logger.error(f"Error in feature search: {str(e)}")
            return []

    def _smart_search(self, session: Session, search_text: str) -> List[Dict]:
        """Smart search that looks everywhere"""
        try:
            # Look for partial matches in addresses
            address_matches = session.query(Property).filter(
                Property.address.ilike(f"%{search_text}%")
            ).limit(5).all()

            # Look for owner names
            owner_matches = session.query(Property).join(Owner).filter(
                Owner.name.ilike(f"%{search_text}%")
            ).limit(5).all()

            # Combine and deduplicate results
            all_properties = list(set(address_matches + owner_matches))
            return [self._format_quick_result(p) for p in all_properties]

        except Exception as e:
            self.logger.error(f"Error in smart search: {str(e)}")
            return []

    def _format_quick_result(self, property: Property) -> Dict:
        """Format property for quick search results"""
        try:
            return {
                "id": property.id,
                "address": property.address,
                "preview": {
                    "value": f"${property.total_value:,}",
                    "type": property.property_type,
                    "size": f"{property.square_feet:,} sqft",
                    "beds_baths": f"{property.bedrooms}b {property.bathrooms}ba"
                },
                "score": f"{property.scores[0].total_score:.0%}" if property.scores else "N/A"
            }
        except Exception as e:
            self.logger.error(f"Error formatting result: {str(e)}")
            return {}

    def _get_quick_actions(self, property: Property) -> List[Dict]:
        """Get contextual quick actions for a property"""
        try:
            actions = [
                {
                    "name": "View on Map",
                    "icon": "map",
                    "action": "view_map"
                },
                {
                    "name": "Contact Owner",
                    "icon": "envelope",
                    "action": "contact_owner"
                },
                {
                    "name": "View History",
                    "icon": "clock",
                    "action": "view_history"
                }
            ]
            
            # Add contextual actions
            if property.scores and property.scores[0].total_score > 0.8:
                actions.append({
                    "name": "High Potential",
                    "icon": "star",
                    "action": "view_potential"
                })
            
            return actions

        except Exception as e:
            self.logger.error(f"Error getting quick actions: {str(e)}")
            return []

    def _get_smart_insights(self, property: Property) -> List[Dict]:
        """Get AI-powered insights about the property"""
        try:
            insights = []
            
            # Value insights
            if property.total_value > 0:
                avg_value = 300000  # This would be calculated
                if property.total_value < avg_value:
                    insights.append({
                        "type": "value",
                        "icon": "trending-down",
                        "text": "Below market value for the area"
                    })

            # Age insights
            if property.year_built:
                age = datetime.now().year - property.year_built
                if age > 50:
                    insights.append({
                        "type": "age",
                        "icon": "clock",
                        "text": "Historic property potential"
                    })

            return insights

        except Exception as e:
            self.logger.error(f"Error getting insights: {str(e)}")
            return []

    def _parse_price(self, price_text: str) -> float:
        """Convert price text to number: '$200k' -> 200000"""
        try:
            # Remove '$' and spaces
            price_text = price_text.replace('$', '').replace(' ', '').lower()
            
            # Handle 'k' and 'm' multipliers
            multiplier = 1
            if price_text.endswith('k'):
                multiplier = 1000
                price_text = price_text[:-1]
            elif price_text.endswith('m'):
                multiplier = 1000000
                price_text = price_text[:-1]
            
            return float(price_text) * multiplier

        except Exception as e:
            self.logger.error(f"Error parsing price: {str(e)}")
            return 0

    def _parse_features(self, feature_text: str) -> Dict:
        """Parse feature text: '3 beds 2 baths 2000 sqft' -> dict"""
        try:
            features = {}
            parts = feature_text.lower().split()
            
            for i, part in enumerate(parts):
                if part in ['bed', 'beds', 'bedroom', 'bedrooms'] and i > 0:
                    features['beds'] = int(parts[i-1])
                elif part in ['bath', 'baths', 'bathroom', 'bathrooms'] and i > 0:
                    features['baths'] = float(parts[i-1])
                elif part in ['sqft', 'sf', 'square'] and i > 0:
                    features['sqft'] = float(parts[i-1])
            
            return features

        except Exception as e:
            self.logger.error(f"Error parsing features: {str(e)}")
            return {}
