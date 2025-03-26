"""
Database management system for property data
"""
from typing import Dict, List, Optional, Any
import asyncpg
import asyncio
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from contextlib import asynccontextmanager

Base = declarative_base()

class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    price = Column(Float)
    description = Column(String)
    features = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PropertyAnalysis(Base):
    __tablename__ = 'property_analyses'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    analysis_type = Column(String)
    results = Column(JSON)
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class PropertyValidation(Base):
    __tablename__ = 'property_validations'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    validation_type = Column(String)
    results = Column(JSON)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._init_db()
        
    def _init_db(self):
        """Initialize database connection"""
        try:
            self.engine = create_async_engine(
                self.config['database_url'],
                echo=self.config.get('debug', False),
                pool_size=self.config.get('pool_size', 5),
                max_overflow=self.config.get('max_overflow', 10)
            )
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        except Exception as e:
            self.logger.error(f"Database initialization error: {str(e)}")
            raise
            
    async def create_tables(self):
        """Create database tables"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            self.logger.error(f"Error creating tables: {str(e)}")
            raise
            
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        session = self.async_session()
        try:
            yield session
        finally:
            await session.close()
            
    async def add_property(self, property_data: Dict) -> int:
        """Add new property to database"""
        try:
            async with self.get_session() as session:
                property = Property(**property_data)
                session.add(property)
                await session.commit()
                await session.refresh(property)
                return property.id
        except Exception as e:
            self.logger.error(f"Error adding property: {str(e)}")
            raise
            
    async def add_analysis(self, analysis_data: Dict) -> int:
        """Add property analysis to database"""
        try:
            async with self.get_session() as session:
                analysis = PropertyAnalysis(**analysis_data)
                session.add(analysis)
                await session.commit()
                await session.refresh(analysis)
                return analysis.id
        except Exception as e:
            self.logger.error(f"Error adding analysis: {str(e)}")
            raise
            
    async def add_validation(self, validation_data: Dict) -> int:
        """Add property validation to database"""
        try:
            async with self.get_session() as session:
                validation = PropertyValidation(**validation_data)
                session.add(validation)
                await session.commit()
                await session.refresh(validation)
                return validation.id
        except Exception as e:
            self.logger.error(f"Error adding validation: {str(e)}")
            raise
            
    async def get_property(self, property_id: int) -> Optional[Dict]:
        """Get property by ID"""
        try:
            async with self.get_session() as session:
                result = await session.get(Property, property_id)
                if result:
                    return {
                        'id': result.id,
                        'address': result.address,
                        'latitude': result.latitude,
                        'longitude': result.longitude,
                        'price': result.price,
                        'description': result.description,
                        'features': result.features,
                        'created_at': result.created_at,
                        'updated_at': result.updated_at
                    }
                return None
        except Exception as e:
            self.logger.error(f"Error getting property: {str(e)}")
            raise
            
    async def get_property_analyses(self, property_id: int) -> List[Dict]:
        """Get all analyses for a property"""
        try:
            async with self.get_session() as session:
                query = select(PropertyAnalysis).where(
                    PropertyAnalysis.property_id == property_id
                )
                result = await session.execute(query)
                analyses = result.scalars().all()
                return [{
                    'id': analysis.id,
                    'property_id': analysis.property_id,
                    'analysis_type': analysis.analysis_type,
                    'results': analysis.results,
                    'score': analysis.score,
                    'created_at': analysis.created_at
                } for analysis in analyses]
        except Exception as e:
            self.logger.error(f"Error getting analyses: {str(e)}")
            raise
            
    async def get_property_validations(self, property_id: int) -> List[Dict]:
        """Get all validations for a property"""
        try:
            async with self.get_session() as session:
                query = select(PropertyValidation).where(
                    PropertyValidation.property_id == property_id
                )
                result = await session.execute(query)
                validations = result.scalars().all()
                return [{
                    'id': validation.id,
                    'property_id': validation.property_id,
                    'validation_type': validation.validation_type,
                    'results': validation.results,
                    'is_valid': validation.is_valid,
                    'created_at': validation.created_at
                } for validation in validations]
        except Exception as e:
            self.logger.error(f"Error getting validations: {str(e)}")
            raise
            
    async def update_property(self, property_id: int, updates: Dict) -> bool:
        """Update property data"""
        try:
            async with self.get_session() as session:
                property = await session.get(Property, property_id)
                if property:
                    for key, value in updates.items():
                        setattr(property, key, value)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Error updating property: {str(e)}")
            raise
            
    async def delete_property(self, property_id: int) -> bool:
        """Delete property and related data"""
        try:
            async with self.get_session() as session:
                property = await session.get(Property, property_id)
                if property:
                    await session.delete(property)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Error deleting property: {str(e)}")
            raise
