#!/usr/bin/env python3
"""
Database initialization script
Creates all tables defined in the SQLAlchemy models
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.db import engine, Base
from app.models.hotel_entities import Hotel, HotelAmenity, HotelImage, Booking, SearchHistory, Room, RoomAmenity, RoomImage
from app.core.logger import logger

def create_tables():
    """Create all database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        # List created tables
        logger.info("Created tables:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"  - {table_name}")
            
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

if __name__ == "__main__":
    create_tables()
