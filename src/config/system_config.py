"""
Comprehensive system configuration with all options
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
import os
import logging
from pathlib import Path
import threading
from datetime import datetime, timedelta

class AutoScalingStrategy(Enum):
    CPU_BASED = 'cpu'
    MEMORY_BASED = 'memory'
    REQUEST_BASED = 'request'
    CUSTOM = 'custom'

class FailoverStrategy(Enum):
    ACTIVE_PASSIVE = 'active_passive'
    ACTIVE_ACTIVE = 'active_active'
    MULTI_REGION = 'multi_region'

class LoadBalancingStrategy(Enum):
    ROUND_ROBIN = 'round_robin'
    LEAST_CONNECTIONS = 'least_connections'
    WEIGHTED = 'weighted'
    GEOLOCATION = 'geolocation'

@dataclass
class SystemBehaviorConfig:
    # Auto-scaling
    auto_scaling_enabled: bool = False
    auto_scaling_strategy: AutoScalingStrategy = AutoScalingStrategy.CPU_BASED
    min_instances: int = 1
    max_instances: int = 10
    scale_up_threshold: float = 0.75
    scale_down_threshold: float = 0.25
    cooldown_period: int = 300
    
    # Failover
    failover_enabled: bool = False
    failover_strategy: FailoverStrategy = FailoverStrategy.ACTIVE_PASSIVE
    failover_regions: List[str] = field(default_factory=list)
    health_check_interval: int = 30
    failover_threshold: int = 3
    
    # Load Balancing
    load_balancing_enabled: bool = False
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    health_check_path: str = '/health'
    session_persistence: bool = True
    ssl_enabled: bool = True
    
    # Circuit Breaker
    circuit_breaker_enabled: bool = False
    failure_threshold: int = 5
    reset_timeout: int = 60
    half_open_timeout: int = 30
    
    # Throttling
    throttling_enabled: bool = False
    rate_limit: int = 1000
    burst_limit: int = 100
    throttling_period: int = 60

@dataclass
class DataManagementConfig:
    # Retention
    retention_enabled: bool = True
    retention_period_days: int = 90
    retention_policy: Dict[str, int] = field(default_factory=dict)
    compliance_enabled: bool = True
    
    # Archival
    archival_enabled: bool = True
    archive_after_days: int = 365
    archive_storage_class: str = 'STANDARD_IA'
    compression_enabled: bool = True
    
    # Backup
    backup_enabled: bool = True
    backup_schedule: str = '0 0 * * *'  # Daily at midnight
    backup_retention_count: int = 30
    incremental_backup: bool = True
    
    # Migration
    migration_enabled: bool = False
    migration_batch_size: int = 1000
    migration_window: str = '00:00-06:00'
    validation_enabled: bool = True
    
    # Version Control
    versioning_enabled: bool = True
    max_versions: int = 10
    prune_versions_after_days: int = 90

@dataclass
class IntegrationConfig:
    # API Versioning
    api_versioning_enabled: bool = True
    current_version: str = 'v1'
    supported_versions: List[str] = field(default_factory=list)
    deprecation_policy: Dict[str, Any] = field(default_factory=dict)
    
    # Service Discovery
    service_discovery_enabled: bool = True
    discovery_mechanism: str = 'consul'
    service_registry: str = 'http://localhost:8500'
    health_check_interval: int = 30
    
    # Circuit Breaker
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    reset_timeout: int = 60
    bulkhead_size: int = 20
    
    # Retry Policies
    retry_enabled: bool = True
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    
    # Timeouts
    connect_timeout: float = 5.0
    read_timeout: float = 30.0
    write_timeout: float = 30.0
    idle_timeout: float = 60.0

@dataclass
class UserExperienceConfig:
    # Notifications
    notification_channels: List[str] = field(default_factory=list)
    notification_preferences: Dict[str, bool] = field(default_factory=dict)
    notification_schedule: Dict[str, List[str]] = field(default_factory=dict)
    
    # Reports
    report_formats: List[str] = field(default_factory=list)
    custom_reports: Dict[str, Any] = field(default_factory=dict)
    report_scheduling: Dict[str, str] = field(default_factory=dict)
    
    # Dashboard
    dashboard_layout: Dict[str, Any] = field(default_factory=dict)
    widget_preferences: Dict[str, Any] = field(default_factory=dict)
    refresh_interval: int = 300
    
    # Localization
    default_language: str = 'en'
    supported_languages: List[str] = field(default_factory=list)
    date_format: str = 'YYYY-MM-DD'
    time_format: str = '24h'
    
    # Accessibility
    high_contrast: bool = False
    font_size: str = 'medium'
    screen_reader_support: bool = True
    keyboard_navigation: bool = True

class SystemConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self._load_config()
        
    def _load_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
                
            self.system_behavior = SystemBehaviorConfig(**config.get('system_behavior', {}))
            self.data_management = DataManagementConfig(**config.get('data_management', {}))
            self.integration = IntegrationConfig(**config.get('integration', {}))
            self.user_experience = UserExperienceConfig(**config.get('user_experience', {}))
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            raise
            
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'system_behavior': self.system_behavior.__dict__,
                'data_management': self.data_management.__dict__,
                'integration': self.integration.__dict__,
                'user_experience': self.user_experience.__dict__
            }
            
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f)
                
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            raise
            
    def update_system_behavior(self, updates: Dict):
        """Update system behavior configuration"""
        for key, value in updates.items():
            if hasattr(self.system_behavior, key):
                setattr(self.system_behavior, key, value)
        self.save_config()
        
    def update_data_management(self, updates: Dict):
        """Update data management configuration"""
        for key, value in updates.items():
            if hasattr(self.data_management, key):
                setattr(self.data_management, key, value)
        self.save_config()
        
    def update_integration(self, updates: Dict):
        """Update integration configuration"""
        for key, value in updates.items():
            if hasattr(self.integration, key):
                setattr(self.integration, key, value)
        self.save_config()
        
    def update_user_experience(self, updates: Dict):
        """Update user experience configuration"""
        for key, value in updates.items():
            if hasattr(self.user_experience, key):
                setattr(self.user_experience, key, value)
        self.save_config()
        
    def get_full_config(self) -> Dict:
        """Get full configuration as dictionary"""
        return {
            'system_behavior': self.system_behavior.__dict__,
            'data_management': self.data_management.__dict__,
            'integration': self.integration.__dict__,
            'user_experience': self.user_experience.__dict__
        }
