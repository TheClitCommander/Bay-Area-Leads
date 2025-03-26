"""
Database service layer for handling database operations
"""
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..models.base import get_db
from ..models.property import Property

class DatabaseService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def save_property(self, property_data: Dict, db: Session) -> Optional[Property]:
        """
        Save property data to database
        
        Args:
            property_data: Dictionary containing property data
            db: Database session
            
        Returns:
            Property object if successful, None if failed
        """
        try:
            # Check if property already exists
            existing_property = db.query(Property).filter(
                Property.parcel_id == property_data.get('parcel_id')
            ).first()
            
            if existing_property:
                # Update existing property
                for key, value in property_data.items():
                    if hasattr(existing_property, key):
                        setattr(existing_property, key, value)
                property_obj = existing_property
            else:
                # Create new property
                property_obj = Property(**property_data)
                db.add(property_obj)
            
            db.commit()
            db.refresh(property_obj)
            return property_obj
            
        except Exception as e:
            self.logger.error(f"Error saving property: {str(e)}")
            db.rollback()
            return None
    
    def get_property_by_parcel_id(self, parcel_id: str, db: Session) -> Optional[Property]:
        """Get property by parcel ID"""
        try:
            return db.query(Property).filter(Property.parcel_id == parcel_id).first()
        except Exception as e:
            self.logger.error(f"Error retrieving property: {str(e)}")
            return None
    
    def get_properties_by_town(self, town: str, db: Session) -> List[Property]:
        """Get all properties in a town"""
        try:
            return db.query(Property).filter(
                Property.property_address.like(f"%{town}%")
            ).all()
        except Exception as e:
            self.logger.error(f"Error retrieving properties for town {town}: {str(e)}")
            return []
    
    def get_delinquent_properties(self, min_amount: float, db: Session) -> List[Property]:
        """Get properties with tax delinquency above minimum amount"""
        try:
            return db.query(Property).filter(
                Property.delinquent_amount >= min_amount
            ).all()
        except Exception as e:
            self.logger.error(f"Error retrieving delinquent properties: {str(e)}")
            return []
    
    def delete_property(self, parcel_id: str, db: Session) -> bool:
        """Delete property by parcel ID"""
        try:
            property_obj = self.get_property_by_parcel_id(parcel_id, db)
            if property_obj:
                db.delete(property_obj)
                db.commit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error deleting property: {str(e)}")
            db.rollback()
            return False
