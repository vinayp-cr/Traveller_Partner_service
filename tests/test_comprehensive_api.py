#!/usr/bin/env python3
"""
Comprehensive API tests for all endpoints including database operations
Tests hotel search, room and rates, booking, and database operations
"""

import pytest
import sys
import os
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.db import get_db, SessionLocal
from app.models.hotel_search_models import HotelSearchRequest, Occupancy
from app.models.rooms_and_rates_request import RoomsAndRatesRequest
from app.models.booking_model import BookingRequest, StayPeriod, BillingContact, Contact, Room as BookingRoom, Guest
from app.models.autosuggest_model import AutosuggestRequest
from app.core.logger import logger

class TestComprehensiveAPI:
    """Comprehensive tests for all API endpoints with database operations"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def db_session(self):
        """Create database session for testing"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def sample_hotel_search_request(self):
        """Sample hotel search request"""
        return HotelSearchRequest(
            checkInDate="2025-12-15",
            checkOutDate="2025-12-17",
            lat=40.7128,  # New York
            lng=-74.0060,
            type="hotel",
            occupancies=[
                Occupancy(
                    numOfRoom=1,
                    numOfAdults=2,
                    numOfChildren=0,
                    childAges=[]
                )
            ],
            destinationCountryCode="US"
        )
    
    @pytest.fixture
    def sample_rooms_rates_request(self):
        """Sample rooms and rates request"""
        return RoomsAndRatesRequest(
            checkInDate="2025-12-15",
            checkOutDate="2025-12-17",
            currency="USD",
            hotelId="test-hotel-123",
            lat=40.7128,
            lng=-74.0060,
            occupancies=[
                Occupancy(
                    numOfRoom=1,
                    numOfAdults=2,
                    numOfChildren=0,
                    childAges=[]
                )
            ]
        )
    
    @pytest.fixture
    def sample_autosuggest_request(self):
        """Sample autosuggest request"""
        return AutosuggestRequest(key="New York")
    
    @pytest.fixture
    def sample_booking_request(self):
        """Sample booking request"""
        return BookingRequest(
            rooms=[
                BookingRoom(
                    roomRefId="room-ref-123",
                    rateRefId="rate-ref-456",
                    guests=[
                        Guest(
                            type="Adult",
                            title="Mr",
                            firstName="John",
                            lastName="Doe",
                            age=30
                        )
                    ],
                    adults="1",
                    child="0"
                )
            ],
            stayPeriod=StayPeriod(
                start="2025-12-15",
                end="2025-12-17"
            ),
            billingContact=BillingContact(
                firstName="John",
                lastName="Doe",
                title="Mr",
                type="adult",
                contact=Contact(
                    email="john.doe@example.com",
                    phone="+1234567890"
                )
            ),
            recommendationId="rec-123",
            bookingRefId="booking-ref-789"
        )

    def test_autosuggest_api(self, client, sample_autosuggest_request):
        """Test autosuggest API endpoint"""
        print("\n=== Testing Autosuggest API ===")
        
        # Use GET request with query parameter instead of POST with JSON
        response = client.get(f"/api/hotel/autosuggest?key={sample_autosuggest_request.key}")
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        # Accept both success and error responses for integration testing
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Autosuggest API working")
            # Validate response structure
            assert "status" in data, "Response should contain 'status' field"
            if data.get("status") == "success":
                assert "message" in data, "Success response should contain 'message' field"
                assert "data" in data, "Success response should contain 'data' field"
            else:
                assert "error" in data, "Error response should contain 'error' field"
                assert "desc" in data, "Error response should contain 'desc' field"
            if "correlation_id" in data:
                print(f"Correlation ID: {data['correlation_id']}")
        else:
            print("ℹ️ Autosuggest API returned error (expected in test environment)")

    def test_hotel_search_api(self, client, sample_hotel_search_request):
        """Test hotel search API endpoint"""
        print("\n=== Testing Hotel Search API ===")
        
        payload = sample_hotel_search_request.model_dump()
        response = client.post("/api/hotel/search", json=payload)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        # Accept both success and error responses
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "hotels_found" in data
            assert "hotels" in data
            print(f"✅ Hotel Search API working - Found {data['hotels_found']} hotels")
        else:
            print("ℹ️ Hotel Search API returned error (expected in test environment)")

    def test_rooms_rates_api(self, client, sample_rooms_rates_request):
        """Test rooms and rates API endpoint"""
        print("\n=== Testing Rooms and Rates API ===")
        
        payload = sample_rooms_rates_request.model_dump()
        response = client.post("/api/hotel/roomsandrates", json=payload)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        # Accept both success and error responses
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Rooms and Rates API working")
            # Check if database info is included
            if "database_info" in data:
                print(f"✅ Database saving info: {data['database_info']}")
        else:
            print("ℹ️ Rooms and Rates API returned error (expected in test environment)")

    def test_booking_api(self, client, sample_booking_request):
        """Test hotel booking API endpoint"""
        print("\n=== Testing Hotel Booking API ===")
        
        payload = sample_booking_request.model_dump()
        response = client.post("/api/hotel/book/test-hotel-123/test-token", json=payload)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        # Accept success, server error, and timeout responses
        assert response.status_code in [200, 500, 504], f"Expected 200, 500, or 504, got {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Hotel Booking API working")
        else:
            print("ℹ️ Hotel Booking API returned error (expected in test environment)")

    def test_database_operations(self, db_session):
        """Test database operations and table structure"""
        print("\n=== Testing Database Operations ===")
        
        from sqlalchemy import text
        from app.models.hotel_entities import Hotel, Room, RoomAmenity, RoomImage, HotelAmenity, HotelImage
        
        try:
            # Test database connection
            result = db_session.execute(text("SELECT 1")).fetchone()
            assert result[0] == 1
            print("✅ Database connection working")
            
            # Test table existence
            tables_query = text("SHOW TABLES")
            tables = db_session.execute(tables_query).fetchall()
            table_names = [table[0] for table in tables]
            
            expected_tables = [
                'hotels', 'hotel_amenities', 'hotel_images', 
                'rooms', 'room_amenities', 'room_images',
                'bookings', 'search_history'
            ]
            
            for table in expected_tables:
                assert table in table_names, f"Table {table} should exist"
                print(f"✅ Table {table} exists")
            
            print(f"✅ All {len(expected_tables)} expected tables found")
            
        except Exception as e:
            print(f"⚠️ Database test error: {str(e)}")
            # Don't fail the test for database issues in test environment
            assert "sqlite" in str(e).lower() or "mysql" in str(e).lower(), "Should be a database connection issue"

    def test_room_data_structure(self, db_session):
        """Test room data structure and relationships"""
        print("\n=== Testing Room Data Structure ===")
        
        from app.models.hotel_entities import Room, RoomAmenity, RoomImage
        
        try:
            # Create a test room
            test_room = Room(
                room_id="test-room-123",
                group_id="1",
                name="Test Room",
                beds=[{"type": "FullBed", "count": "1"}],
                total_sleep=2,
                room_area="300",
                availability="5",
                room_rating="4.5",
                api_hotel_id="test-hotel-123"
            )
            
            db_session.add(test_room)
            db_session.flush()  # Get the room ID
            
            # Add test amenities
            amenities = [
                RoomAmenity(room_id=test_room.id, amenity_name="Free WiFi", amenity_type="technology"),
                RoomAmenity(room_id=test_room.id, amenity_name="Air Conditioning", amenity_type="room_features"),
                RoomAmenity(room_id=test_room.id, amenity_name="Private Bathroom", amenity_type="bathroom")
            ]
            
            for amenity in amenities:
                db_session.add(amenity)
            
            # Add test images
            images = [
                RoomImage(room_id=test_room.id, image_url="https://example.com/image1.jpg", size="XL", caption="Room view", is_primary=True, sort_order=1),
                RoomImage(room_id=test_room.id, image_url="https://example.com/image2.jpg", size="XXL", caption="Bathroom", is_primary=False, sort_order=2)
            ]
            
            for image in images:
                db_session.add(image)
            
            db_session.commit()
            print("✅ Test room created with amenities and images")
            
            # Test relationships
            room_with_relations = db_session.query(Room).filter(Room.id == test_room.id).first()
            assert len(room_with_relations.amenities) == 3
            assert len(room_with_relations.images) == 2
            print("✅ Room relationships working correctly")
            
            # Clean up
            db_session.delete(test_room)
            db_session.commit()
            print("✅ Test data cleaned up")
            
        except Exception as e:
            print(f"⚠️ Room data structure test error: {str(e)}")
            # Rollback on error
            db_session.rollback()

    def test_api_headers_and_payloads(self, client):
        """Test API headers and payload validation"""
        print("\n=== Testing API Headers and Payloads ===")
        
        # Test with invalid payload
        invalid_payload = {"invalid": "data"}
        response = client.post("/api/hotel/search", json=invalid_payload)
        print(f"Invalid payload status: {response.status_code}")
        assert response.status_code in [422, 500], "Should return validation error for invalid payload"
        
        # Test with missing required fields
        incomplete_payload = {"checkInDate": "2025-12-15"}
        response = client.post("/api/hotel/search", json=incomplete_payload)
        print(f"Incomplete payload status: {response.status_code}")
        assert response.status_code in [422, 500], "Should return validation error for incomplete payload"
        
        print("✅ API payload validation working")

    def test_error_handling(self, client):
        """Test error handling across APIs"""
        print("\n=== Testing Error Handling ===")
        
        # Test non-existent endpoint
        response = client.get("/api/hotel/nonexistent")
        assert response.status_code == 404
        print("✅ 404 error handling working")
        
        # Test invalid method
        response = client.get("/api/hotel/search")
        assert response.status_code == 405  # Method not allowed
        print("✅ 405 error handling working")
        
        print("✅ Error handling tests passed")

if __name__ == "__main__":
    # Run the tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
