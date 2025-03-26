"""
Integrated property data processing system
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging
from .performance_optimizer import PerformanceOptimizer, PropertyTextChunker
from .error_recovery import ErrorRecovery
from .advanced_validation import AdvancedValidator, ValidationResult, ValidationSeverity
from .quality_reporter import QualityReporter

class PropertyProcessor:
    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # Initialize components
        self.optimizer = PerformanceOptimizer(
            max_workers=self.config.get('max_workers', 4),
            cache_size=self.config.get('cache_size', 1000)
        )
        self.chunker = PropertyTextChunker(
            chunk_size=self.config.get('chunk_size', 1000)
        )
        self.error_recovery = ErrorRecovery()
        self.validator = AdvancedValidator()
        self.quality_reporter = QualityReporter(
            output_dir=self.config.get('report_dir', 'reports')
        )
        
        # Initialize metrics
        self.processing_stats = {
            'start_time': None,
            'end_time': None,
            'total_properties': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'recovered_properties': 0,
            'validation_issues': {
                'info': 0,
                'warning': 0,
                'error': 0
            }
        }
        
    def process_document(self, text: str) -> Dict:
        """Process a document containing property data"""
        try:
            self.processing_stats['start_time'] = datetime.now()
            
            # Split document into chunks
            chunks = self.chunker.chunk_text(text)
            
            # Process chunks in parallel
            properties = self.optimizer.process_pages_parallel(
                chunks,
                self._process_chunk
            )
            
            # Generate quality report
            report_path = self.quality_reporter.generate_report({
                'processing_stats': self.processing_stats,
                'performance_stats': self.optimizer.get_performance_stats(),
                'validation_summary': self._get_validation_summary()
            })
            
            self.processing_stats['end_time'] = datetime.now()
            
            return {
                'properties': properties,
                'stats': self.processing_stats,
                'report_path': report_path
            }
            
        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            return {
                'error': str(e),
                'stats': self.processing_stats
            }
        finally:
            self.optimizer.cleanup()
            
    def _process_chunk(self, chunk: str) -> List[Dict]:
        """Process a chunk of text into property records"""
        properties = []
        
        try:
            # Extract individual property records
            property_texts = self.chunker.extract_properties(chunk)
            
            for text in property_texts:
                try:
                    # Extract property data
                    property_dict = self.optimizer.parse_text_cached(text)
                    
                    if not property_dict:
                        # Attempt recovery
                        property_dict = self._attempt_recovery(text)
                        
                    if property_dict:
                        # Validate property data
                        validation_results = self.validator.validate_property(property_dict)
                        
                        # Track validation issues
                        self._track_validation_issues(validation_results)
                        
                        # Add validation results to property data
                        property_dict['validation_results'] = [
                            {
                                'field': r.field,
                                'message': r.message,
                                'severity': r.severity.value
                            }
                            for r in validation_results
                        ]
                        
                        properties.append(property_dict)
                        self.processing_stats['successful_extractions'] += 1
                    else:
                        self.processing_stats['failed_extractions'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Error processing property text: {str(e)}")
                    self.processing_stats['failed_extractions'] += 1
                    
        except Exception as e:
            self.logger.error(f"Error processing chunk: {str(e)}")
            
        return properties
        
    def _attempt_recovery(self, text: str) -> Optional[Dict]:
        """Attempt to recover property data from problematic text"""
        try:
            property_dict = {}
            
            # Try to recover essential fields
            for field in ['account_number', 'owner_name', 'address']:
                value = self.error_recovery.attempt_recovery(field, text)
                if value:
                    property_dict[field] = value
                    
            if property_dict:
                self.processing_stats['recovered_properties'] += 1
                
            return property_dict if len(property_dict) >= 2 else None
            
        except Exception as e:
            self.logger.error(f"Error in recovery attempt: {str(e)}")
            return None
            
    def _track_validation_issues(self, results: List[ValidationResult]):
        """Track validation issues by severity"""
        for result in results:
            self.processing_stats['validation_issues'][result.severity.value] += 1
            
    def _get_validation_summary(self) -> Dict:
        """Get summary of validation issues"""
        return {
            'total_issues': sum(self.processing_stats['validation_issues'].values()),
            'by_severity': self.processing_stats['validation_issues'],
            'success_rate': (
                self.processing_stats['successful_extractions'] /
                (self.processing_stats['total_properties'] or 1)
            ) * 100
        }
