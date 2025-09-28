#!/usr/bin/env python3
"""
Test chatbot with different messages
"""

import requests
import json

def test_chatbot():
    test_messages = [
        'hotels',
        'find hotels',
        'I want hotels',
        'hotels in New York',
        'I want to find hotels in New York'
    ]

    for i, message in enumerate(test_messages):
        try:
            response = requests.post('http://localhost:8000/api/chat/message', 
                                   json={'message': message})
            print(f'Test {i+1}: "{message}"')
            print(f'Status: {response.status_code}')
            if 'error' in response.text.lower():
                print(f'❌ Error: {response.text}')
            else:
                print(f'✅ Success: {response.json().get("message", "No message")}')
            print('-' * 50)
        except Exception as e:
            print(f'Exception: {str(e)}')
            print('-' * 50)

if __name__ == "__main__":
    test_chatbot()
