"""
Database initialization script
"""
import logging
from pathlib import Path
from .base import Base, engine

def init_database():
    """Initialize the database"""
    try:
        # Create database directory if it doesn't exist
        db_dir = Path(__file__).parent.parent.parent / 'data'
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logging.info("Database initialized successfully")
        
    except Exception as e:
        logging.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
