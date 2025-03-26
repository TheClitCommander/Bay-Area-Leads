"""
Property model for database
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base

class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True)
    parcel_id = Column(String, unique=True, index=True)
    owner_name = Column(String)
    property_address = Column(String)
    mailing_address = Column(String)
    
    # Assessment Data
    land_value = Column(Float)
    building_value = Column(Float)
    total_value = Column(Float)
    assessment_year = Column(String)
    
    # Tax Data
    annual_tax = Column(Float)
    tax_rate = Column(Float)
    payment_status = Column(String)
    last_payment_date = Column(DateTime)
    delinquent_amount = Column(Float, default=0.0)
    
    # Property Details
    land_area = Column(Float)
    building_area = Column(Float)
    year_built = Column(String)
    zoning = Column(String)
    property_class = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_data = Column(JSON)  # Store original scraped data
    
    # Relationships will be added here for:
    # - Tax History
    # - Sales History
    # - Market Data
    # - Geographic Data
    
    def __repr__(self):
        return f"<Property {self.parcel_id}: {self.property_address}>"
    
    def to_dict(self):
        """Convert property to dictionary"""
        return {
            'id': self.id,
            'parcel_id': self.parcel_id,
            'owner_name': self.owner_name,
            'property_address': self.property_address,
            'mailing_address': self.mailing_address,
            'assessment_data': {
                'land_value': self.land_value,
                'building_value': self.building_value,
                'total_value': self.total_value,
                'assessment_year': self.assessment_year
            },
            'tax_data': {
                'annual_tax': self.annual_tax,
                'tax_rate': self.tax_rate,
                'payment_status': self.payment_status,
                'last_payment_date': self.last_payment_date,
                'delinquent_amount': self.delinquent_amount
            },
            'property_details': {
                'land_area': self.land_area,
                'building_area': self.building_area,
                'year_built': self.year_built,
                'zoning': self.zoning,
                'property_class': self.property_class
            }
        }
