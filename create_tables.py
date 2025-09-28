#!/usr/bin/env python3
"""
Script to create chatbot database tables
"""

from app.core.db import Base, engine
from app.ai.chatbot.models.chat_models import ChatSession, ChatMessage, BookingContext
from sqlalchemy import text

def main():
    print('Creating chatbot database tables...')
    print('=' * 50)

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine, tables=[
            ChatSession.__table__,
            ChatMessage.__table__,
            BookingContext.__table__
        ])
        
        print('✅ Chatbot tables created successfully!')
        print('Created tables:')
        print('- chat_sessions')
        print('- chat_messages') 
        print('- booking_context')
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'chat_%'"))
            tables = result.fetchall()
            
            print(f'✅ Verified {len(tables)} chatbot tables exist:')
            for table in tables:
                print(f'  - {table[0]}')
        
        print('🎉 Chatbot database setup completed successfully!')
        
    except Exception as e:
        print(f'❌ Error creating chatbot tables: {str(e)}')

if __name__ == "__main__":
    main()
