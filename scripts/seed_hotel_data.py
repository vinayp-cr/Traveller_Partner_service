#!/usr/bin/env python3
"""
Hotel Data Seeding Script
Populates database with hotel data for filtering functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.services.data_population_service import DataPopulationService
from app.api.services.hotel_service import HotelService

async def seed_popular_cities():
    """Seed database with popular cities for hotel searches"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize services
        hotel_service = HotelService()
        data_service = DataPopulationService(hotel_service)
        
        print("🏨 Starting hotel data seeding...")
        
        # Popular cities to seed with coordinates
        cities_to_seed = [
            {"city": "New York", "state": "NY", "country": "US", "lat": 40.7128, "lng": -74.0060, "max_hotels": 50},
            {"city": "Los Angeles", "state": "CA", "country": "US", "lat": 34.0522, "lng": -118.2437, "max_hotels": 50},
            {"city": "Chicago", "state": "IL", "country": "US", "lat": 41.8781, "lng": -87.6298, "max_hotels": 40},
            {"city": "Miami", "state": "FL", "country": "US", "lat": 25.7617, "lng": -80.1918, "max_hotels": 40},
            {"city": "Las Vegas", "state": "NV", "country": "US", "lat": 36.1699, "lng": -115.1398, "max_hotels": 50},
            {"city": "San Francisco", "state": "CA", "country": "US", "lat": 37.7749, "lng": -122.4194, "max_hotels": 40},
            {"city": "Boston", "state": "MA", "country": "US", "lat": 42.3601, "lng": -71.0589, "max_hotels": 30},
            {"city": "Seattle", "state": "WA", "country": "US", "lat": 47.6062, "lng": -122.3321, "max_hotels": 30},
            {"city": "Orlando", "state": "FL", "country": "US", "lat": 28.5383, "lng": -81.3792, "max_hotels": 50},
            {"city": "Atlanta", "state": "GA", "country": "US", "lat": 33.7490, "lng": -84.3880, "max_hotels": 30}
        ]
        
        print(f"📊 Seeding {len(cities_to_seed)} cities...")
        
        # Process each city
        for i, city_data in enumerate(cities_to_seed, 1):
            city_name = city_data["city"]
            print(f"\n🏙️  Processing {i}/{len(cities_to_seed)}: {city_name}, {city_data['state']}")
            
            try:
                result = await data_service.populate_hotels_for_city(
                    db=db,
                    city=city_data["city"],
                    state=city_data["state"],
                    country=city_data["country"],
                    max_hotels=city_data["max_hotels"]
                )
                
                if result.get("status") == "success":
                    hotels_count = result.get("hotels_count", 0)
                    print(f"✅ {city_name}: {hotels_count} hotels saved")
                else:
                    print(f"❌ {city_name}: {result.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ {city_name}: Error - {str(e)}")
                continue
        
        # Get final statistics
        print("\n📈 Getting final statistics...")
        stats = await data_service.get_population_stats(db=db)
        
        if stats.get("status") == "success":
            stats_data = stats.get("statistics", {})
            print(f"\n🎉 Seeding completed!")
            print(f"📊 Final Statistics:")
            print(f"   🏨 Hotels: {stats_data.get('hotels', 0)}")
            print(f"   🛏️  Rooms: {stats_data.get('rooms', 0)}")
            print(f"   🏊 Hotel Amenities: {stats_data.get('hotel_amenities', 0)}")
            print(f"   🛁 Room Amenities: {stats_data.get('room_amenities', 0)}")
            print(f"   📸 Hotel Images: {stats_data.get('hotel_images', 0)}")
            print(f"   🖼️  Room Images: {stats_data.get('room_images', 0)}")
            print(f"   ⭐ Star Ratings: {list(stats_data.get('star_rating_distribution', {}).keys())}")
            print(f"   🏷️  Amenity Types: {stats_data.get('amenity_types', [])}")
        else:
            print(f"❌ Error getting statistics: {stats.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Seeding failed: {str(e)}")
        raise
    finally:
        db.close()

async def seed_single_city(city: str, state: str = None, country: str = "US", max_hotels: int = 50, lat: float = None, lng: float = None):
    """Seed a single city"""
    
    # Get database session
    db = next(get_db())
    
    try:
        # Initialize services
        hotel_service = HotelService()
        data_service = DataPopulationService(hotel_service)
        
        print(f"🏨 Seeding hotel data for {city}, {state}, {country}...")
        
        result = await data_service.populate_hotels_for_city(
            db=db,
            city=city,
            state=state,
            country=country,
            lat=lat,
            lng=lng,
            max_hotels=max_hotels
        )
        
        if result.get("status") == "success":
            hotels_count = result.get("hotels_count", 0)
            print(f"✅ Successfully seeded {hotels_count} hotels for {city}")
        else:
            print(f"❌ Failed to seed {city}: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error seeding {city}: {str(e)}")
        raise
    finally:
        db.close()

def main():
    """Main function to run the seeding script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed hotel data for filtering functionality")
    parser.add_argument("--city", help="City name to seed")
    parser.add_argument("--state", help="State name")
    parser.add_argument("--country", default="US", help="Country code (default: US)")
    parser.add_argument("--lat", type=float, help="Latitude coordinate")
    parser.add_argument("--lng", type=float, help="Longitude coordinate")
    parser.add_argument("--max-hotels", type=int, default=50, help="Maximum hotels to fetch (default: 50)")
    parser.add_argument("--all-cities", action="store_true", help="Seed all popular cities")
    
    args = parser.parse_args()
    
    if args.all_cities:
        print("🌍 Seeding all popular cities...")
        asyncio.run(seed_popular_cities())
    elif args.city:
        print(f"🏙️  Seeding single city: {args.city}")
        asyncio.run(seed_single_city(args.city, args.state, args.country, args.max_hotels, args.lat, args.lng))
    else:
        print("❌ Please specify --city or --all-cities")
        parser.print_help()

if __name__ == "__main__":
    main()
