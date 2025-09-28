#!/usr/bin/env python3
"""
Script to create chatbot database tables
"""

import pymysql
import json
from pathlib import Path
from sqlalchemy import create_engine, text
from app.core.db import Base, engine
from app.ai.chatbot.models.chat_models import ChatSession, ChatMessage, BookingContext


def create_chatbot_tables():
    """Create chatbot database tables"""
    try:
        print("Creating chatbot database tables...")
        print("=" * 50)
        
        # Create all tables
        Base.metadata.create_all(bind=engine, tables=[
            ChatSession.__table__,
            ChatMessage.__table__,
            BookingContext.__table__
        ])
        
        print("✅ Chatbot tables created successfully!")
        print("\nCreated tables:")
        print("- chat_sessions")
        print("- chat_messages") 
        print("- booking_context")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'chat_%'"))
            tables = result.fetchall()
            
            print(f"\n✅ Verified {len(tables)} chatbot tables exist:")
            for table in tables:
                print(f"  - {table[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating chatbot tables: {str(e)}")
        return False


def main():
    """Main function"""
    print("Chatbot Database Setup")
    print("=" * 50)
    
    success = create_chatbot_tables()
    
    if success:
        print("\n🎉 Chatbot database setup completed successfully!")
        print("\nYou can now:")
        print("1. Start the application: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("2. Access the chatbot at: http://localhost:8000/chatbot")
        print("3. Test the API at: http://localhost:8000/docs")
    else:
        print("\n❌ Chatbot database setup failed!")
        print("Please check the error messages above and try again.")


if __name__ == "__main__":
    main()