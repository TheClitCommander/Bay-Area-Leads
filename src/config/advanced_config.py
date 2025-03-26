"""
Advanced configuration management system
"""
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import yaml
import json
import os
import logging
import logging.config
from pathlib import Path
from datetime import datetime, timedelta
import threading
import watchdog.events
import watchdog.observers
from cryptography.fernet import Fernet

class CacheStrategy(Enum):
    NONE = 'none'
    LRU = 'lru'
    LFU = 'lfu'
    TIERED = 'tiered'
    ADAPTIVE = 'adaptive'

class StorageType(Enum):
    LOCAL = 'local'
    S3 = 's3'
    GCS = 'gcs'
    AZURE = 'azure'

class ProcessingMode(Enum):
    SYNC = 'sync'
    ASYNC = 'async'
    BATCH = 'batch'
    STREAMING = 'streaming'

@dataclass
class MLConfig:
    enabled: bool = False
    model_path: str = ''
    batch_size: int = 32
    threshold: float = 0.5
    use_gpu: bool = False
    model_update_frequency: str = 'weekly'
    feature_columns: List[str] = field(default_factory=list)
    target_column: str = ''
    
@dataclass
class SecurityConfig:
    encryption_key: str = ''
    ssl_enabled: bool = True
    ssl_cert_path: str = ''
    ssl_key_path: str = ''
    allowed_ips: List[str] = field(default_factory=list)
    rate_limit: int = 100
    token_expiry: int = 3600
    password_policy: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MonitoringConfig:
    enabled: bool = True
    metrics_port: int = 9090
    tracing_enabled: bool = False
    log_level: str = 'INFO'
    alert_thresholds: Dict[str, float] = field(default_factory=dict)
    retention_days: int = 30
    dashboard_enabled: bool = True

@dataclass
class DistributedConfig:
    enabled: bool = False
    cluster_nodes: List[str] = field(default_factory=list)
    heartbeat_interval: int = 30
    sync_strategy: str = 'eventual'
    leader_election: bool = False
    partition_count: int = 1
    replication_factor: int = 1

class AdvancedConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        self.observers = []
        self.encryption_key = None
        
        # Initialize configuration
        self._init_config()
        
        # Setup file watching
        self._setup_file_watching()
        
    def _init_config(self):
        """Initialize configuration system"""
        try:
            # Load base configuration
            self.config = self._load_config()
            
            # Initialize encryption
            self._init_encryption()
            
            # Setup monitoring
            self._setup_monitoring()
            
        except Exception as e:
            self.logger.error(f"Error initializing config: {str(e)}")
            raise
            
    def _init_encryption(self):
        """Initialize encryption for sensitive data"""
        try:
            if not os.path.exists('.key'):
                key = Fernet.generate_key()
                with open('.key', 'wb') as f:
                    f.write(key)
            else:
                with open('.key', 'rb') as f:
                    key = f.read()
                    
            self.encryption_key = Fernet(key)
            
        except Exception as e:
            self.logger.error(f"Error initializing encryption: {str(e)}")
            
    def _setup_monitoring(self):
        """Setup configuration monitoring"""
        try:
            monitoring_config = self.get_monitoring_config()
            if monitoring_config.enabled:
                # Setup metrics endpoint
                from prometheus_client import start_http_server
                start_http_server(monitoring_config.metrics_port)
                
                # Setup tracing if enabled
                if monitoring_config.tracing_enabled:
                    import opentelemetry.trace as trace
                    trace.set_tracer_provider(trace.TracerProvider())
                    
        except Exception as e:
            self.logger.error(f"Error setting up monitoring: {str(e)}")
            
    def _setup_file_watching(self):
        """Setup configuration file watching"""
        try:
            class ConfigHandler(watchdog.events.FileSystemEventHandler):
                def __init__(self, callback):
                    self.callback = callback
                    
                def on_modified(self, event):
                    if event.src_path == self.config_path:
                        self.callback()
                        
            observer = watchdog.observers.Observer()
            observer.schedule(
                ConfigHandler(self._reload_config),
                os.path.dirname(self.config_path)
            )
            observer.start()
            self.observers.append(observer)
            
        except Exception as e:
            self.logger.error(f"Error setting up file watching: {str(e)}")
            
    def _reload_config(self):
        """Reload configuration from file"""
        with self.lock:
            try:
                self.config = self._load_config()
                self.logger.info("Configuration reloaded")
                
                # Notify observers
                for observer in self.observers:
                    observer.on_config_changed(self.config)
                    
            except Exception as e:
                self.logger.error(f"Error reloading config: {str(e)}")
                
    def get_ml_config(self) -> MLConfig:
        """Get machine learning configuration"""
        config = self.config.get('ml', {})
        return MLConfig(
            enabled=config.get('enabled', False),
            model_path=config.get('model_path', ''),
            batch_size=config.get('batch_size', 32),
            threshold=config.get('threshold', 0.5),
            use_gpu=config.get('use_gpu', False),
            model_update_frequency=config.get('model_update_frequency', 'weekly'),
            feature_columns=config.get('feature_columns', []),
            target_column=config.get('target_column', '')
        )
        
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        config = self.config.get('security', {})
        return SecurityConfig(
            encryption_key=self._decrypt(config.get('encryption_key', '')),
            ssl_enabled=config.get('ssl_enabled', True),
            ssl_cert_path=config.get('ssl_cert_path', ''),
            ssl_key_path=config.get('ssl_key_path', ''),
            allowed_ips=config.get('allowed_ips', []),
            rate_limit=config.get('rate_limit', 100),
            token_expiry=config.get('token_expiry', 3600),
            password_policy=config.get('password_policy', {
                'min_length': 8,
                'require_special': True,
                'require_numbers': True,
                'require_uppercase': True
            })
        )
        
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        config = self.config.get('monitoring', {})
        return MonitoringConfig(
            enabled=config.get('enabled', True),
            metrics_port=config.get('metrics_port', 9090),
            tracing_enabled=config.get('tracing_enabled', False),
            log_level=config.get('log_level', 'INFO'),
            alert_thresholds=config.get('alert_thresholds', {}),
            retention_days=config.get('retention_days', 30),
            dashboard_enabled=config.get('dashboard_enabled', True)
        )
        
    def get_distributed_config(self) -> DistributedConfig:
        """Get distributed system configuration"""
        config = self.config.get('distributed', {})
        return DistributedConfig(
            enabled=config.get('enabled', False),
            cluster_nodes=config.get('cluster_nodes', []),
            heartbeat_interval=config.get('heartbeat_interval', 30),
            sync_strategy=config.get('sync_strategy', 'eventual'),
            leader_election=config.get('leader_election', False),
            partition_count=config.get('partition_count', 1),
            replication_factor=config.get('replication_factor', 1)
        )
        
    def get_cache_config(self) -> Dict:
        """Get cache configuration"""
        return {
            'strategy': CacheStrategy[self.config.get('cache', {}).get('strategy', 'LRU')],
            'max_size': self.config.get('cache', {}).get('max_size', 1000),
            'ttl': self.config.get('cache', {}).get('ttl', 3600),
            'persist': self.config.get('cache', {}).get('persist', False),
            'compression': self.config.get('cache', {}).get('compression', False),
            'backup_count': self.config.get('cache', {}).get('backup_count', 1)
        }
        
    def get_storage_config(self) -> Dict:
        """Get storage configuration"""
        return {
            'type': StorageType[self.config.get('storage', {}).get('type', 'LOCAL')],
            'path': self.config.get('storage', {}).get('path', 'data'),
            'backup_enabled': self.config.get('storage', {}).get('backup_enabled', True),
            'compression_level': self.config.get('storage', {}).get('compression_level', 6),
            'chunk_size': self.config.get('storage', {}).get('chunk_size', 1024 * 1024)
        }
        
    def get_processing_config(self) -> Dict:
        """Get processing configuration"""
        return {
            'mode': ProcessingMode[self.config.get('processing', {}).get('mode', 'SYNC')],
            'batch_size': self.config.get('processing', {}).get('batch_size', 100),
            'timeout': self.config.get('processing', {}).get('timeout', 30),
            'retry_count': self.config.get('processing', {}).get('retry_count', 3),
            'parallel': self.config.get('processing', {}).get('parallel', True)
        }
        
    def update_config(self, section: str, updates: Dict):
        """Update configuration section"""
        with self.lock:
            try:
                if section not in self.config:
                    self.config[section] = {}
                    
                # Update configuration
                self.config[section].update(updates)
                
                # Encrypt sensitive data
                if section == 'security':
                    updates = self._encrypt_sensitive_data(updates)
                    
                # Save to file
                self._save_config()
                
                # Notify observers
                for observer in self.observers:
                    observer.on_config_changed(self.config)
                    
            except Exception as e:
                self.logger.error(f"Error updating config: {str(e)}")
                raise
                
    def add_observer(self, observer):
        """Add configuration change observer"""
        self.observers.append(observer)
        
    def remove_observer(self, observer):
        """Remove configuration change observer"""
        self.observers.remove(observer)
        
    def _encrypt_sensitive_data(self, data: Dict) -> Dict:
        """Encrypt sensitive configuration data"""
        try:
            if self.encryption_key:
                for key, value in data.items():
                    if key in ['encryption_key', 'api_key', 'secret_key']:
                        data[key] = self._encrypt(value)
            return data
        except Exception as e:
            self.logger.error(f"Error encrypting data: {str(e)}")
            return data
            
    def _encrypt(self, value: str) -> str:
        """Encrypt a value"""
        if self.encryption_key and value:
            return self.encryption_key.encrypt(value.encode()).decode()
        return value
        
    def _decrypt(self, value: str) -> str:
        """Decrypt a value"""
        if self.encryption_key and value:
            return self.encryption_key.decrypt(value.encode()).decode()
        return value
        
    def _save_config(self):
        """Save configuration to file"""
        try:
            # Create backup
            backup_path = f"{self.config_path}.bak"
            if os.path.exists(self.config_path):
                os.rename(self.config_path, backup_path)
                
            # Save new config
            with open(self.config_path, 'w') as f:
                if self.config_path.endswith('.yaml'):
                    yaml.dump(self.config, f)
                else:
                    json.dump(self.config, f, indent=2)
                    
            # Remove backup
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            self.logger.error(f"Error saving config: {str(e)}")
            # Restore backup
            if os.path.exists(backup_path):
                os.rename(backup_path, self.config_path)
            raise
            
    def cleanup(self):
        """Cleanup resources"""
        for observer in self.observers:
            observer.stop()
        for observer in self.observers:
            observer.join()
