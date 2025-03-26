"""
Models for tracking property history
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class TaxHistory(Base):
    __tablename__ = 'tax_history'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    tax_year = Column(String)
    amount_due = Column(Float)
    amount_paid = Column(Float)
    payment_date = Column(DateTime)
    tax_rate = Column(Float)
    assessment_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    property = relationship("Property", back_populates="tax_history")

class SalesHistory(Base):
    __tablename__ = 'sales_history'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    sale_date = Column(DateTime)
    sale_price = Column(Float)
    buyer_name = Column(String)
    seller_name = Column(String)
    sale_type = Column(String)  # e.g., 'Market', 'Foreclosure', 'Short Sale'
    days_on_market = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    property = relationship("Property", back_populates="sales_history")
