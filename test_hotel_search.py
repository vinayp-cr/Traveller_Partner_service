#!/usr/bin/env python3
"""
Test script for Hotel Search API
This script tests the hotel search implementation.
"""

import asyncio
import json
from app.models.hotel_search_models import HotelSearchRequest, Occupancy, SortCriteria, Filters

def create_test_request():
    """Create a test request for hotel search"""
    
    # Create occupancy
    occupancy = Occupancy(
        adults=1,
        childs=0,
        childages=[]
    )
    
    # Create sort criteria
    sort_criteria = SortCriteria(
        key="price",
        order="asc"
    )
    
    # Create filters (optional)
    filters = Filters(
        ratings=[4, 5],  # 4 and 5 star hotels
        amenities=["WiFi", "Parking"]
    )
    
    # Create the main request
    request = HotelSearchRequest(
        checkin_date="2024-02-15",
        checkout_date="2024-02-17",
        occupancy=[occupancy],
        country_of_residence="US",
        place_id="test_place_123",
        lat=37.7749,  # San Francisco coordinates
        lng=-122.4194,
        radius=50,
        sort=[sort_criteria],
        filters=filters,
        is_async=False
    )
    
    return request

def test_request_serialization():
    """Test that the request can be serialized to JSON"""
    request = create_test_request()
    
    # Convert to dict
    request_dict = request.model_dump(exclude_none=True)
    
    print("Test Request (JSON):")
    print(json.dumps(request_dict, indent=2))
    
    # Test that it can be converted back
    reconstructed = HotelSearchRequest(**request_dict)
    print("\nRequest reconstructed successfully!")
    
    return request_dict

def test_api_url_construction():
    """Test the API URL construction"""
    base_url = "https://uat.travelapi.ai"
    endpoint = "/hotels/api/v2/properties"
    query_params = {
        "currency": "USD",
        "page": 1,
        "limit": 50,
        "amenities": "true"
    }
    
    import urllib.parse
    query_string = urllib.parse.urlencode(query_params)
    full_url = f"{base_url}{endpoint}?{query_string}"
    
    print(f"\nConstructed API URL:")
    print(full_url)
    
    return full_url

if __name__ == "__main__":
    print("Testing Hotel Search V2 Implementation")
    print("=" * 50)
    
    # Test request creation and serialization
    test_request_serialization()
    
    # Test URL construction
    test_api_url_construction()
    
    print("\nAll tests completed successfully!")
    print("\nTo test the actual API, you can use the following endpoint:")
    print("POST /api/hotel/search - Hotel search API")
    print("\nExample usage:")
    print("curl -X POST 'http://localhost:8000/api/hotel/search' \\")
    print("  -H 'Content-Type: application/json' \\")
    print("  -H 'x-correlation-id: your-correlation-id' \\")
    print("  -d '{\"checkin_date\": \"2024-02-15\", \"checkout_date\": \"2024-02-17\", ...}'")
    print("\nNote: x-correlation-id header is required and should be obtained from the autosuggest API response.")
