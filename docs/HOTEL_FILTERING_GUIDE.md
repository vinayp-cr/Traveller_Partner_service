# 🏨 Hotel Filtering System Guide

This guide explains how to populate hotel data and implement filtering functionality for your hotel search application.

## 📊 Database Schema Overview

### Core Tables for Filtering:

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `hotels` | Basic hotel info | `name`, `city`, `star_rating`, `avg_rating` |
| `hotel_amenities` | Hotel facilities | `amenity_name`, `amenity_type` |
| `hotel_images` | Hotel photos | `image`, `is_primary` |
| `hotel_rooms` | Room details & pricing | `base_rate`, `total_rate`, `published_rate` |
| `room_amenities` | Room-specific amenities | `amenity_name`, `amenity_type` |
| `room_images` | Room photos | `image_url`, `size` |

## 🚀 Data Population Methods

### Method 1: API-Driven Population (Recommended)

Use your existing Xeni API integration to populate data:

```bash
# 1. Search and save hotels for a city
curl -X POST "http://localhost:8000/api/hotel/search-and-save" \
  -H "Content-Type: application/json" \
  -H "x-correlation-id: your-correlation-id" \
  -d '{
    "place_id": "New York,NY,US",
    "lat": 40.7128,
    "lng": -74.0060,
    "currency": "USD",
    "page": 1,
    "limit": 50,
    "amenities": true
  }'

# 2. Get pricing and save room data (requires availability token)
curl -X GET "http://localhost:8000/api/hotel/price-and-save?availability_token=YOUR_TOKEN&currency=USD" \
  -H "x-correlation-id: your-correlation-id"
```

### Method 2: Bulk Data Loading

Use the new data population endpoints:

```bash
# Populate a single city
curl -X POST "http://localhost:8000/api/data/populate-city" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "New York",
    "state": "NY",
    "country": "US",
    "max_hotels": 50
  }'

# Populate multiple cities
curl -X POST "http://localhost:8000/api/data/populate-multiple-cities" \
  -H "Content-Type: application/json" \
  -d '{
    "cities": [
      {"city": "New York", "state": "NY", "country": "US", "max_hotels": 50},
      {"city": "Los Angeles", "state": "CA", "country": "US", "max_hotels": 50}
    ]
  }'

# Populate popular US cities
curl -X POST "http://localhost:8000/api/data/populate-popular-cities"
```

### Method 3: Script-Based Seeding

Use the provided seeding script:

```bash
# Seed all popular cities
python scripts/seed_hotel_data.py --all-cities

# Seed a specific city
python scripts/seed_hotel_data.py --city "New York" --state "NY" --max-hotels 50
```

## 🔍 Filtering Implementation

### Available Filter Endpoints:

#### 1. Filter Hotels
```bash
curl -X POST "http://localhost:8000/api/hotel/filter" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "New York",
    "star_rating": [4, 5],
    "amenities": ["wifi", "pool", "gym"],
    "min_price": 100,
    "max_price": 500,
    "min_rating": 4.0,
    "page": 1,
    "limit": 20
  }'
```

#### 2. Get Filter Options
```bash
# Get all available filter options
curl -X GET "http://localhost:8000/api/hotel/filter-options"

# Get available amenities
curl -X GET "http://localhost:8000/api/hotel/amenities"

# Get available cities
curl -X GET "http://localhost:8000/api/hotel/cities?country=US"
```

#### 3. Get Population Statistics
```bash
curl -X GET "http://localhost:8000/api/data/population-stats"
```

## 🎯 Filter Criteria Supported

### 1. **Location Filters**
- `city`: Filter by city name
- `state`: Filter by state
- `country`: Filter by country

### 2. **Star Rating Filters**
- `star_rating`: Array of star ratings [3, 4, 5]

### 3. **Amenity Filters**
- `amenities`: Array of amenity names ["wifi", "pool", "gym"]
- Supports both hotel and room amenities

### 4. **Price Filters**
- `min_price`: Minimum room rate
- `max_price`: Maximum room rate
- Based on `base_rate` from `hotel_rooms` table

### 5. **Rating Filters**
- `min_rating`: Minimum average rating
- `max_rating`: Maximum average rating
- Based on `avg_rating` from `hotels` table

### 6. **Pagination**
- `page`: Page number (default: 1)
- `limit`: Results per page (default: 20)

## 📱 Frontend Integration Example

### JavaScript/React Example:

```javascript
// Filter hotels
const filterHotels = async (filters) => {
  const response = await fetch('/api/hotel/filter', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      city: filters.city,
      star_rating: filters.starRating,
      amenities: filters.amenities,
      min_price: filters.minPrice,
      max_price: filters.maxPrice,
      min_rating: filters.minRating,
      page: filters.page || 1,
      limit: filters.limit || 20
    })
  });
  
  return await response.json();
};

// Get filter options
const getFilterOptions = async () => {
  const response = await fetch('/api/hotel/filter-options');
  return await response.json();
};

// Usage
const filters = {
  city: "New York",
  starRating: [4, 5],
  amenities: ["wifi", "pool"],
  minPrice: 100,
  maxPrice: 500,
  minRating: 4.0
};

const results = await filterHotels(filters);
console.log(`Found ${results.total_count} hotels`);
```

## 🗄️ Database Optimization

### Recommended Indexes:

```sql
-- For location filtering
CREATE INDEX idx_hotels_city ON hotels(city);
CREATE INDEX idx_hotels_state ON hotels(state);
CREATE INDEX idx_hotels_country ON hotels(country);

-- For rating filtering
CREATE INDEX idx_hotels_star_rating ON hotels(star_rating);
CREATE INDEX idx_hotels_avg_rating ON hotels(avg_rating);

-- For amenity filtering
CREATE INDEX idx_hotel_amenities_name ON hotel_amenities(amenity_name);
CREATE INDEX idx_hotel_amenities_type ON hotel_amenities(amenity_type);

-- For price filtering
CREATE INDEX idx_rooms_base_rate ON hotel_rooms(base_rate);
CREATE INDEX idx_rooms_hotel_id ON hotel_rooms(hotel_id);
```

## 🔧 Configuration

### Environment Variables:
```bash
# Database connection
DATABASE_URL=mysql+pymysql://user:password@host:port/database

# Xeni API configuration
XENI_API_KEY=your_api_key
XENI_SECRET_KEY=your_secret_key
```

### API Configuration:
The system uses `app/config/api_config.json` for API endpoints and settings.

## 📊 Monitoring

### Check Population Status:
```bash
# Get current statistics
curl -X GET "http://localhost:8000/api/data/population-stats"

# Response example:
{
  "status": "success",
  "statistics": {
    "hotels": 500,
    "rooms": 1200,
    "hotel_amenities": 2500,
    "room_amenities": 1800,
    "hotel_images": 1500,
    "room_images": 3000,
    "amenity_types": ["general", "room", "hotel"],
    "star_rating_distribution": {
      "3": 100,
      "4": 250,
      "5": 150
    }
  }
}
```

## 🚨 Troubleshooting

### Common Issues:

1. **No Data Found**: Ensure you've populated the database first
2. **Slow Queries**: Add database indexes for frequently filtered fields
3. **Memory Issues**: Use pagination for large result sets
4. **API Errors**: Check Xeni API credentials and rate limits

### Debug Commands:

```bash
# Test database connection
python -c "from app.core.db import get_db; print('DB OK')"

# Test API endpoints
curl -X GET "http://localhost:8000/health"

# Check population status
curl -X GET "http://localhost:8000/api/data/population-stats"
```

## 🎉 Next Steps

1. **Populate Data**: Use the seeding script or API endpoints
2. **Test Filters**: Try different filter combinations
3. **Optimize**: Add database indexes based on usage patterns
4. **Monitor**: Track query performance and data quality
5. **Scale**: Consider caching for frequently accessed data

This system provides a robust foundation for hotel filtering functionality with comprehensive data population and flexible filtering options.
