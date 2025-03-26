"""
Base model configuration for SQLAlchemy
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from pathlib import Path
import os

# Create base class for declarative models
Base = declarative_base()

# Create database engine
db_path = Path(__file__).parent.parent.parent / 'data' / 'database.sqlite'
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
