# Travel Assistant Chatbot

A conversational AI chatbot for hotel search and booking, integrated with the Travel Partner Service API.

## Features

### 🤖 **Core Chatbot Features**
- **Natural Language Processing**: Intent recognition and entity extraction
- **Conversational Flow**: Multi-step conversation management
- **Context Awareness**: Maintains conversation state and booking context
- **Smart Suggestions**: Contextual response suggestions

### 🏨 **Hotel Integration**
- **Hotel Search**: Search hotels by location, dates, and guest count
- **Advanced Filtering**: Filter by amenities, price range, and ratings
- **Real-time Booking**: Book hotels through integrated APIs
- **Booking Management**: Cancel and modify bookings

### 💬 **Conversation Capabilities**
- **Location Search**: "I want to stay in New York"
- **Date Selection**: "This weekend" or "December 15-17"
- **Guest Information**: "2 adults, 1 room"
- **Amenity Filtering**: "Breakfast included" or "Swimming pool"
- **Price Filtering**: "Under $200" or "Budget hotels"
- **Booking Actions**: "Book this hotel" or "Cancel my booking"

## API Endpoints

### Chat Endpoints
- `POST /api/chat/message` - Send message to chatbot
- `GET /api/chat/session/{session_id}` - Get session information
- `GET /api/chat/session/{session_id}/history` - Get chat history
- `POST /api/chat/session/{session_id}/reset` - Reset session
- `GET /api/chat/sessions` - Get active sessions
- `DELETE /api/chat/session/{session_id}` - Delete session
- `GET /api/chat/health` - Health check

### Web Interface
- `GET /chatbot` - Chatbot web interface

## Quick Start

### 1. Setup Database
```bash
python create_chatbot_tables.py
```

### 2. Start Application
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Access Chatbot
- **Web Interface**: http://localhost:8000/chatbot
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/chat/health

## Usage Examples

### Basic Hotel Search
```
User: "I want to book a hotel in New York"
Bot: "Perfect! I'll search for hotels in New York. When would you like to check in and check out?"
User: "This weekend"
Bot: "Great! I have your dates: 2024-12-15 to 2024-12-17. How many guests and rooms do you need?"
User: "2 adults, 1 room"
Bot: "Perfect! I found 5 hotels for you: [hotel list]"
```

### Filtering and Booking
```
User: "Show me hotels with breakfast included"
Bot: "Here are hotels with breakfast: [filtered list]"
User: "Book the first hotel"
Bot: "Congratulations! Your hotel has been booked successfully!"
```

## Architecture

### 📁 **Project Structure**
```
app/ai/chatbot/
├── models/              # Data models
│   ├── chat_models.py   # Chat session, message models
│   └── intent_models.py # Intent recognition models
├── services/            # Business logic
│   ├── chat_service.py  # Main chat processing
│   ├── intent_service.py # NLP and intent recognition
│   └── hotel_integration_service.py # Hotel API integration
├── controllers/         # API endpoints
│   └── chat_controller.py
├── repositories/        # Database operations
│   └── chat_repository.py
└── utils/              # Helper functions
    ├── nlp_utils.py    # NLP utilities
    └── response_builder.py # Response formatting
```

### 🔄 **Conversation Flow**
1. **Greeting** → User initiates conversation
2. **Location** → Bot asks for destination
3. **Dates** → Bot asks for check-in/out dates
4. **Guests** → Bot asks for guest count
5. **Search** → Bot searches for hotels
6. **Filtering** → User can filter results
7. **Booking** → User selects and books hotel
8. **Completion** → Booking confirmed

### 🧠 **Intent Recognition**
- **Pattern Matching**: Regex-based intent detection
- **Entity Extraction**: Location, dates, numbers, amenities
- **Context Awareness**: Maintains conversation state
- **Confidence Scoring**: Ranks intent matches

## Configuration

### Environment Variables
```bash
# Database configuration (inherited from main app)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_NAME=travel_partner

# Chatbot configuration
CHATBOT_ENABLED=true
CHATBOT_SESSION_TIMEOUT=3600
CHATBOT_MAX_MESSAGES=100
```

### Database Tables
- **chat_sessions**: Chat session management
- **chat_messages**: Message history
- **booking_context**: Conversation state

## Integration

### With Existing APIs
The chatbot integrates seamlessly with existing hotel APIs:
- **Hotel Search**: Uses `HotelService.search_hotels()`
- **Hotel Booking**: Uses `HotelService.book_hotel()`
- **Hotel Cancellation**: Uses `HotelService.cancel_booking()`
- **Terrapay Integration**: Inherits payment processing

### With React Frontend
The chatbot provides REST APIs that can be easily integrated:
- **Session Management**: Create and manage chat sessions
- **Message Processing**: Send messages and receive responses
- **Context Persistence**: Maintain conversation state
- **Real-time Updates**: WebSocket support (future enhancement)

## Development

### Adding New Intents
1. Add intent pattern to `IntentService._load_intent_patterns()`
2. Add entity patterns to `IntentService._load_entity_patterns()`
3. Implement handler in `ChatService._process_intent()`
4. Add response templates to `ResponseBuilder`

### Adding New Features
1. Create service method in appropriate service class
2. Add API endpoint in `ChatController`
3. Update conversation flow in `ChatService`
4. Add UI components to `chatbot.html`

## Testing

### Manual Testing
1. Start the application
2. Open http://localhost:8000/chatbot
3. Test conversation flow:
   - Search for hotels
   - Apply filters
   - Book a hotel
   - Cancel booking

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/api/chat/health

# Test message endpoint
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to book a hotel in New York"}'
```

## Future Enhancements

### Phase 2 Features
- **Voice Integration**: Speech-to-text and text-to-speech
- **Multi-language Support**: Internationalization
- **Advanced NLP**: Machine learning-based intent recognition
- **Personalization**: User preferences and history
- **WebSocket Support**: Real-time messaging
- **Mobile App**: Native mobile interface

### Phase 3 Features
- **AI Recommendations**: ML-based hotel recommendations
- **Sentiment Analysis**: Emotion detection and response
- **Conversation Analytics**: Usage insights and optimization
- **Integration APIs**: Third-party service integrations
- **Advanced Booking**: Complex booking scenarios

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the health endpoint at `/api/chat/health`
3. Check application logs for error details
4. Verify database connectivity and table creation

## License

This chatbot is part of the Travel Partner Service and follows the same licensing terms.
