#!/usr/bin/env python3
"""
Fix chatbot database and test functionality
"""

from app.core.db import engine, Base
from app.ai.chatbot.models.chat_models import ChatSession, ChatMessage, BookingContext
from sqlalchemy import text

def main():
    print('Checking and fixing chatbot database...')
    print('=' * 50)

    try:
        # Check if tables exist
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES LIKE 'chat_%'"))
            tables = result.fetchall()
            
            print(f'Found {len(tables)} chatbot tables:')
            for table in tables:
                print(f'  - {table[0]}')
            
            if len(tables) == 0:
                print('No chatbot tables found. Creating them...')
                
                # Create tables
                Base.metadata.create_all(bind=engine, tables=[
                    ChatSession.__table__,
                    ChatMessage.__table__,
                    BookingContext.__table__
                ])
                
                print('✅ Chatbot tables created successfully!')
                
                # Verify tables were created
                result = conn.execute(text("SHOW TABLES LIKE 'chat_%'"))
                tables = result.fetchall()
                print(f'✅ Verified {len(tables)} chatbot tables exist:')
                for table in tables:
                    print(f'  - {table[0]}')
            else:
                print('✅ Chatbot tables already exist!')
        
        print('\n🎉 Database setup completed!')
        
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
