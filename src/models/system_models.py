"""
Models for system metadata and collection tracking
"""
from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Table
from sqlalchemy.orm import relationship
from .base import Base

class DataSource(Base):
    __tablename__ = 'data_sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    source_type = Column(String)  # gis, assessor, clerk, etc.
    url = Column(String)
    
    # Authentication
    auth_type = Column(String)  # none, api_key, oauth, etc.
    auth_config = Column(JSON)  # Encrypted authentication details
    
    # Rate Limiting
    rate_limit = Column(Integer)  # requests per minute
    cooldown_period = Column(Integer)  # minutes between bulk collections
    
    # Collection Config
    collection_schedule = Column(String)  # cron expression
    batch_size = Column(Integer)
    timeout = Column(Integer)  # seconds
    retry_count = Column(Integer)
    
    # Relationships
    collections = relationship("CollectionRun", back_populates="source")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_tested = Column(DateTime)
    is_active = Column(Boolean, default=True)

class CollectionRun(Base):
    __tablename__ = 'collection_runs'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('data_sources.id'))
    
    # Run Details
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String)  # running, completed, failed
    
    # Statistics
    total_records = Column(Integer)
    new_records = Column(Integer)
    updated_records = Column(Integer)
    failed_records = Column(Integer)
    
    # Performance
    duration_seconds = Column(Float)
    average_response_time = Column(Float)
    rate_limit_hits = Column(Integer)
    
    # Errors and Warnings
    error_count = Column(Integer)
    error_details = Column(JSON)
    warning_count = Column(Integer)
    warning_details = Column(JSON)
    
    # Relationships
    source = relationship("DataSource", back_populates="collections")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class DataValidation(Base):
    __tablename__ = 'data_validations'
    
    id = Column(Integer, primary_key=True)
    collection_run_id = Column(Integer, ForeignKey('collection_runs.id'))
    
    # Validation Details
    validation_type = Column(String)  # format, completeness, consistency
    field_name = Column(String)
    expected_format = Column(String)
    
    # Results
    passed = Column(Boolean)
    fail_reason = Column(String)
    affected_records = Column(Integer)
    
    # Sample Data
    sample_failures = Column(JSON)  # List of example failures
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemConfig(Base):
    __tablename__ = 'system_configs'
    
    id = Column(Integer, primary_key=True)
    config_key = Column(String, unique=True)
    config_value = Column(JSON)
    
    # Validation
    data_type = Column(String)  # string, number, json, etc.
    validation_rules = Column(JSON)
    
    # Access Control
    requires_encryption = Column(Boolean, default=False)
    restricted = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String)
    updated_by = Column(String)

class ProcessingJob(Base):
    __tablename__ = 'processing_jobs'
    
    id = Column(Integer, primary_key=True)
    job_type = Column(String)  # collect, process, analyze, etc.
    
    # Job Config
    parameters = Column(JSON)
    priority = Column(Integer)
    max_retries = Column(Integer)
    
    # Execution
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(String)  # pending, running, completed, failed
    current_retry = Column(Integer, default=0)
    
    # Results
    result_summary = Column(JSON)
    error_details = Column(JSON)
    
    # Resources
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    disk_usage = Column(Float)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class APIUsage(Base):
    __tablename__ = 'api_usage'
    
    id = Column(Integer, primary_key=True)
    endpoint = Column(String)
    method = Column(String)  # GET, POST, etc.
    
    # Usage Stats
    timestamp = Column(DateTime)
    response_time = Column(Float)
    status_code = Column(Integer)
    
    # Request Details
    ip_address = Column(String)
    user_agent = Column(String)
    request_params = Column(JSON)
    
    # Rate Limiting
    rate_limit_remaining = Column(Integer)
    rate_limit_reset = Column(DateTime)
    
    # Errors
    error_type = Column(String)
    error_message = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
