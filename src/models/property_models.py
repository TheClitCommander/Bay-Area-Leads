"""
Core database models for property data
"""
from datetime import datetime
from typing import List
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Table
from sqlalchemy.orm import relationship
from .base import Base

class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, unique=True, index=True)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zipcode = Column(String)
    
    # Property Details
    property_type = Column(String)  # residential, commercial, etc.
    land_use_code = Column(String)
    year_built = Column(Integer)
    square_feet = Column(Float)
    lot_size = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    units = Column(Integer)
    
    # Assessment Data
    land_value = Column(Float)
    building_value = Column(Float)
    total_value = Column(Float)
    last_assessment_date = Column(DateTime)
    
    # GIS Data
    latitude = Column(Float)
    longitude = Column(Float)
    geometry = Column(JSON)  # Store GeoJSON
    flood_zone = Column(String)
    zone_code = Column(String)
    
    # Relationships
    owner_id = Column(Integer, ForeignKey('owners.id'))
    owner = relationship("Owner", back_populates="properties")
    transactions = relationship("Transaction", back_populates="property")
    permits = relationship("Permit", back_populates="property")
    violations = relationship("Violation", back_populates="property")
    scores = relationship("PropertyScore", back_populates="property")
    utilities = relationship("UtilityRecord", back_populates="property")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_collected_at = Column(DateTime)
    data_completeness = Column(Float)  # Score from 0-1
    collection_errors = Column(JSON)

class Owner(Base):
    __tablename__ = 'owners'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    mailing_address = Column(String)
    owner_type = Column(String)  # individual, business, trust, etc.
    
    # Business Info (if applicable)
    business_name = Column(String)
    business_type = Column(String)
    license_numbers = Column(JSON)  # List of business licenses
    
    # Relationships
    properties = relationship("Property", back_populates="owner")
    
    # Contact Info
    phone = Column(String)
    email = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified_at = Column(DateTime)

class Transaction(Base):
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    
    # Transaction Details
    transaction_type = Column(String)  # sale, foreclosure, tax lien, etc.
    date = Column(DateTime)
    price = Column(Float)
    seller = Column(String)
    buyer = Column(String)
    
    # Document Info
    document_type = Column(String)  # deed, lien, etc.
    document_number = Column(String)
    book_page = Column(String)
    
    # Relationships
    property = relationship("Property", back_populates="transactions")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    source = Column(String)
    verified = Column(Boolean, default=False)

class Permit(Base):
    __tablename__ = 'permits'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    
    # Permit Details
    permit_type = Column(String)
    permit_number = Column(String)
    description = Column(String)
    status = Column(String)
    
    # Dates
    issue_date = Column(DateTime)
    expiration_date = Column(DateTime)
    completed_date = Column(DateTime)
    
    # Project Info
    contractor = Column(String)
    estimated_cost = Column(Float)
    final_cost = Column(Float)
    
    # Relationships
    property = relationship("Property", back_populates="permits")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Violation(Base):
    __tablename__ = 'violations'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    
    # Violation Details
    violation_type = Column(String)
    description = Column(String)
    status = Column(String)
    severity = Column(String)
    
    # Dates
    reported_date = Column(DateTime)
    inspection_date = Column(DateTime)
    resolution_date = Column(DateTime)
    
    # Resolution
    resolution_description = Column(String)
    fines = Column(Float)
    paid = Column(Boolean, default=False)
    
    # Relationships
    property = relationship("Property", back_populates="violations")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PropertyScore(Base):
    __tablename__ = 'property_scores'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    
    # Scores
    total_score = Column(Float)
    occupation_type = Column(String)  # landlord, business_owner, etc.
    confidence_score = Column(Float)
    
    # Score Components
    value_score = Column(Float)
    location_score = Column(Float)
    condition_score = Column(Float)
    potential_score = Column(Float)
    risk_score = Column(Float)
    
    # Score Details
    score_factors = Column(JSON)  # Detailed breakdown of scoring
    missing_data = Column(JSON)  # List of missing data points
    
    # Relationships
    property = relationship("Property", back_populates="scores")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UtilityRecord(Base):
    __tablename__ = 'utility_records'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    
    # Utility Details
    utility_type = Column(String)  # water, electric, gas, etc.
    account_number = Column(String)
    service_status = Column(String)
    
    # Usage Data
    usage = Column(Float)
    units = Column(String)
    reading_date = Column(DateTime)
    
    # Payment Info
    amount_due = Column(Float)
    payment_status = Column(String)
    last_payment_date = Column(DateTime)
    
    # Relationships
    property = relationship("Property", back_populates="utilities")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
