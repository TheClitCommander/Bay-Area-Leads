"""
Configuration management system
"""
from typing import Dict, Any, Optional
import yaml
import json
import os
from dataclasses import dataclass
from enum import Enum
import logging
import logging.config
from pathlib import Path

class LogLevel(Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class OptimizationLevel(Enum):
    NONE = 0
    BASIC = 1
    AGGRESSIVE = 2
    MAXIMUM = 3

@dataclass
class ProcessingConfig:
    batch_size: int = 100
    thread_count: int = 4
    memory_limit_mb: int = 1024
    cache_size: int = 1000
    timeout_seconds: int = 300

@dataclass
class ValidationConfig:
    severity_levels: Dict[str, int]
    custom_rules: Dict[str, Dict]
    thresholds: Dict[str, float]
    skip_rules: List[str]

@dataclass
class IntegrationConfig:
    api_endpoints: Dict[str, str]
    auth_settings: Dict[str, Dict]
    export_formats: List[str]
    retry_count: int = 3
    timeout_seconds: int = 30

@dataclass
class LoggingConfig:
    level: LogLevel
    format: str
    file_path: Optional[str]
    max_size_mb: int = 100
    backup_count: int = 5

@dataclass
class PerformanceConfig:
    optimization_level: OptimizationLevel
    parallel_processing: bool = True
    cache_strategy: str = 'lru'
    prefetch_enabled: bool = True
    compression_enabled: bool = True

@dataclass
class RecoveryConfig:
    max_retries: int = 3
    fallback_patterns: Dict[str, List[str]]
    error_threshold: float = 0.1
    backup_enabled: bool = True

@dataclass
class ReportingConfig:
    formats: List[str]
    frequency: str
    destinations: Dict[str, str]
    templates: Dict[str, str]

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize logging
        self._setup_logging()
        
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_path) as f:
                if self.config_path.endswith('.yaml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            raise Exception(f"Error loading config: {str(e)}")
            
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.get_logging_config()
        
        logging_dict = {
            'version': 1,
            'formatters': {
                'standard': {
                    'format': log_config.format
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard',
                    'level': log_config.level.value
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console'],
                    'level': log_config.level.value
                }
            }
        }
        
        if log_config.file_path:
            logging_dict['handlers']['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_config.file_path,
                'maxBytes': log_config.max_size_mb * 1024 * 1024,
                'backupCount': log_config.backup_count,
                'formatter': 'standard',
                'level': log_config.level.value
            }
            logging_dict['loggers']['']['handlers'].append('file')
            
        logging.config.dictConfig(logging_dict)
        
    def get_processing_config(self) -> ProcessingConfig:
        """Get processing configuration"""
        config = self.config.get('processing', {})
        return ProcessingConfig(
            batch_size=config.get('batch_size', 100),
            thread_count=config.get('thread_count', 4),
            memory_limit_mb=config.get('memory_limit_mb', 1024),
            cache_size=config.get('cache_size', 1000),
            timeout_seconds=config.get('timeout_seconds', 300)
        )
        
    def get_validation_config(self) -> ValidationConfig:
        """Get validation configuration"""
        config = self.config.get('validation', {})
        return ValidationConfig(
            severity_levels=config.get('severity_levels', {
                'error': 2,
                'warning': 1,
                'info': 0
            }),
            custom_rules=config.get('custom_rules', {}),
            thresholds=config.get('thresholds', {
                'value_change': 0.5,
                'area_difference': 0.1
            }),
            skip_rules=config.get('skip_rules', [])
        )
        
    def get_integration_config(self) -> IntegrationConfig:
        """Get integration configuration"""
        config = self.config.get('integration', {})
        return IntegrationConfig(
            api_endpoints=config.get('api_endpoints', {}),
            auth_settings=config.get('auth_settings', {}),
            export_formats=config.get('export_formats', ['csv', 'json', 'excel']),
            retry_count=config.get('retry_count', 3),
            timeout_seconds=config.get('timeout_seconds', 30)
        )
        
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        config = self.config.get('logging', {})
        return LoggingConfig(
            level=LogLevel[config.get('level', 'INFO')],
            format=config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file_path=config.get('file_path'),
            max_size_mb=config.get('max_size_mb', 100),
            backup_count=config.get('backup_count', 5)
        )
        
    def get_performance_config(self) -> PerformanceConfig:
        """Get performance configuration"""
        config = self.config.get('performance', {})
        return PerformanceConfig(
            optimization_level=OptimizationLevel[config.get('optimization_level', 'BASIC')],
            parallel_processing=config.get('parallel_processing', True),
            cache_strategy=config.get('cache_strategy', 'lru'),
            prefetch_enabled=config.get('prefetch_enabled', True),
            compression_enabled=config.get('compression_enabled', True)
        )
        
    def get_recovery_config(self) -> RecoveryConfig:
        """Get recovery configuration"""
        config = self.config.get('recovery', {})
        return RecoveryConfig(
            max_retries=config.get('max_retries', 3),
            fallback_patterns=config.get('fallback_patterns', {}),
            error_threshold=config.get('error_threshold', 0.1),
            backup_enabled=config.get('backup_enabled', True)
        )
        
    def get_reporting_config(self) -> ReportingConfig:
        """Get reporting configuration"""
        config = self.config.get('reporting', {})
        return ReportingConfig(
            formats=config.get('formats', ['pdf', 'html', 'excel']),
            frequency=config.get('frequency', 'daily'),
            destinations=config.get('destinations', {}),
            templates=config.get('templates', {})
        )
        
    def update_config(self, section: str, updates: Dict):
        """Update configuration section"""
        try:
            if section not in self.config:
                self.config[section] = {}
                
            self.config[section].update(updates)
            
            # Save to file
            with open(self.config_path, 'w') as f:
                if self.config_path.endswith('.yaml'):
                    yaml.dump(self.config, f)
                else:
                    json.dump(self.config, f, indent=2)
                    
            # Reload configuration
            self.config = self._load_config()
            
            # Reinitialize logging if logging config was updated
            if section == 'logging':
                self._setup_logging()
                
        except Exception as e:
            self.logger.error(f"Error updating config: {str(e)}")
            raise
            
    def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            'processing': {
                'batch_size': 100,
                'thread_count': 4,
                'memory_limit_mb': 1024,
                'cache_size': 1000,
                'timeout_seconds': 300
            },
            'validation': {
                'severity_levels': {
                    'error': 2,
                    'warning': 1,
                    'info': 0
                },
                'custom_rules': {},
                'thresholds': {
                    'value_change': 0.5,
                    'area_difference': 0.1
                },
                'skip_rules': []
            },
            'integration': {
                'api_endpoints': {},
                'auth_settings': {},
                'export_formats': ['csv', 'json', 'excel'],
                'retry_count': 3,
                'timeout_seconds': 30
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file_path': 'logs/app.log',
                'max_size_mb': 100,
                'backup_count': 5
            },
            'performance': {
                'optimization_level': 'BASIC',
                'parallel_processing': True,
                'cache_strategy': 'lru',
                'prefetch_enabled': True,
                'compression_enabled': True
            },
            'recovery': {
                'max_retries': 3,
                'fallback_patterns': {},
                'error_threshold': 0.1,
                'backup_enabled': True
            },
            'reporting': {
                'formats': ['pdf', 'html', 'excel'],
                'frequency': 'daily',
                'destinations': {},
                'templates': {}
            }
        }
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Write default config
        with open(self.config_path, 'w') as f:
            if self.config_path.endswith('.yaml'):
                yaml.dump(default_config, f)
            else:
                json.dump(default_config, f, indent=2)
