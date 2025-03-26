"""
Enhanced property processor with comprehensive features
"""
from typing import Dict, List
import asyncio
import logging
from datetime import datetime
from ..validators.comprehensive_validator import ComprehensiveValidator
from ..integrations.comprehensive_integrations import ComprehensiveIntegrations
from ..config.system_config import SystemConfig

class EnhancedPropertyProcessor:
    def __init__(self, config_path: str):
        self.config = SystemConfig(config_path)
        self.validator = ComprehensiveValidator(self.config.get_full_config())
        self.integrations = ComprehensiveIntegrations(self.config.get_full_config())
        self.logger = logging.getLogger(__name__)

    async def process_property(self, property_data: Dict) -> Dict:
        """Process a property with all enhanced features"""
        try:
            # Enrich property data with external information
            enriched_data = await self._enrich_property_data(property_data)
            
            # Validate all aspects
            validation_results = self._validate_property(enriched_data)
            
            # Generate comprehensive analysis
            analysis = self._analyze_property(enriched_data, validation_results)
            
            return {
                'property_data': enriched_data,
                'validation': validation_results,
                'analysis': analysis
            }
            
        except Exception as e:
            self.logger.error(f"Error processing property: {str(e)}")
            raise

    async def _enrich_property_data(self, property_data: Dict) -> Dict:
        """Enrich property data with external information"""
        try:
            # Get location data
            location_data = await self.integrations.get_location_data(
                property_data['latitude'],
                property_data['longitude']
            )
            
            # Process images if available
            image_analysis = {}
            if property_data.get('images'):
                image_analysis = await self.integrations.process_property_images(
                    property_data['images']
                )
            
            # Analyze description
            description_analysis = {}
            if property_data.get('description'):
                description_analysis = await self.integrations.analyze_property_description(
                    property_data['description']
                )
            
            # Get financial data
            financial_data = await self.integrations.get_financial_services(property_data)
            
            # Get community data
            community_data = await self.integrations.get_community_data({
                'lat': property_data['latitude'],
                'lon': property_data['longitude']
            })
            
            # Combine all data
            return {
                **property_data,
                'location_data': location_data,
                'image_analysis': image_analysis,
                'description_analysis': description_analysis,
                'financial_data': financial_data,
                'community_data': community_data
            }
            
        except Exception as e:
            self.logger.error(f"Error enriching property data: {str(e)}")
            raise

    def _validate_property(self, property_data: Dict) -> Dict:
        """Validate all aspects of the property"""
        try:
            return {
                'legal': self.validator.validate_legal_regulatory(property_data),
                'financial': self.validator.validate_financial(property_data),
                'environmental': self.validator.validate_environmental(property_data),
                'technical': self.validator.validate_technical(property_data)
            }
        except Exception as e:
            self.logger.error(f"Error validating property: {str(e)}")
            raise

    def _analyze_property(self, property_data: Dict, validation_results: Dict) -> Dict:
        """Generate comprehensive property analysis"""
        try:
            return {
                'summary': self._generate_summary(property_data, validation_results),
                'investment_potential': self._analyze_investment_potential(property_data),
                'market_position': self._analyze_market_position(property_data),
                'risk_assessment': self._analyze_risks(property_data, validation_results),
                'recommendations': self._generate_recommendations(property_data, validation_results)
            }
        except Exception as e:
            self.logger.error(f"Error analyzing property: {str(e)}")
            raise

    def _generate_summary(self, property_data: Dict, validation_results: Dict) -> Dict:
        """Generate property summary"""
        warnings = []
        highlights = []
        
        # Add validation warnings
        for category, results in validation_results.items():
            warnings.extend(results)
        
        # Add highlights from property data
        if property_data.get('image_analysis', {}).get('features'):
            highlights.extend(property_data['image_analysis']['features'])
            
        if property_data.get('description_analysis', {}).get('features'):
            highlights.extend(property_data['description_analysis']['features'])
            
        return {
            'highlights': highlights,
            'warnings': warnings,
            'score': self._calculate_property_score(property_data, validation_results)
        }

    def _analyze_investment_potential(self, property_data: Dict) -> Dict:
        """Analyze investment potential"""
        financial_data = property_data.get('financial_data', {})
        location_data = property_data.get('location_data', {})
        
        return {
            'roi_potential': financial_data.get('investment_analysis', {}).get('roi', 0),
            'market_trend': location_data.get('market_trends', {}),
            'rental_potential': financial_data.get('rental_analysis', {}),
            'appreciation_forecast': financial_data.get('appreciation_forecast', {})
        }

    def _analyze_market_position(self, property_data: Dict) -> Dict:
        """Analyze market position"""
        location_data = property_data.get('location_data', {})
        community_data = property_data.get('community_data', {})
        
        return {
            'price_comparison': location_data.get('price_comparison', {}),
            'market_demand': location_data.get('market_demand', {}),
            'neighborhood_rating': community_data.get('stats', {}).get('rating', 0),
            'future_development': community_data.get('stats', {}).get('development_plans', [])
        }

    def _analyze_risks(self, property_data: Dict, validation_results: Dict) -> Dict:
        """Analyze property risks"""
        return {
            'legal_risks': [w for w in validation_results.get('legal', [])],
            'financial_risks': [w for w in validation_results.get('financial', [])],
            'environmental_risks': [w for w in validation_results.get('environmental', [])],
            'technical_risks': [w for w in validation_results.get('technical', [])]
        }

    def _generate_recommendations(self, property_data: Dict, validation_results: Dict) -> List[str]:
        """Generate property recommendations"""
        recommendations = []
        
        # Add recommendations based on validation results
        for category, warnings in validation_results.items():
            for warning in warnings:
                recommendations.append(f"Address {category} issue: {warning}")
                
        # Add recommendations based on property analysis
        if property_data.get('financial_data', {}).get('investment_analysis', {}).get('roi', 0) > 0.1:
            recommendations.append("Consider investment opportunity due to high ROI potential")
            
        if property_data.get('location_data', {}).get('market_trends', {}).get('growth_rate', 0) > 0.05:
            recommendations.append("Area showing strong growth potential")
            
        return recommendations

    def _calculate_property_score(self, property_data: Dict, validation_results: Dict) -> float:
        """Calculate overall property score"""
        try:
            base_score = 100
            
            # Deduct points for warnings
            warning_count = sum(len(warnings) for warnings in validation_results.values())
            base_score -= warning_count * 5
            
            # Add points for positive features
            if property_data.get('image_analysis', {}).get('features'):
                base_score += len(property_data['image_analysis']['features']) * 2
                
            if property_data.get('financial_data', {}).get('investment_analysis', {}).get('roi', 0) > 0.1:
                base_score += 10
                
            return max(0, min(100, base_score))
            
        except Exception:
            return 0
