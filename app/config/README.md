# API Configuration

This directory contains the configuration files for the Xeni Hotelier Integration API.

## Configuration Files

### `api_config.json`

This JSON file contains all the API configuration settings including:

- **API URLs**: Base URL and all endpoint paths
- **Headers**: Default headers including x-api-key and accept-language
- **Timeouts**: Request timeout settings
- **Pagination**: Default pagination settings

## Configuration Structure

```json
{
  "api": {
    "base_url": "https://uat.travelapi.ai",
    "endpoints": {
      "autosuggest": "/api/ext/hotel/autosuggest",
      "hotel_search": "/api/ext/hotelSearch",
      "rooms_and_rates": "/api/ext/hotel/roomsandrates",
      "booking_details": "/api/ext/hotel/getBookingDetails",
      "price_recommendation": "/api/ext/hotel/{hotel_id}/{api_token}/price/recommendation/{recommendation_id}",
      "booking_cancellation_fee": "/bookingCancellationFee",
      "cancel_booking": "/booking/cancel"
    }
  },
  "headers": {
    "default": {
      "x-api-key": "6427cfae-3889-49c0-8e46-07400d404f83",
      "accept-language": "en",
      "content-type": "application/json"
    },
    "required_headers": [
      "x-api-key",
      "accept-language"
    ]
  },
  "timeouts": {
    "default": 30.0,
    "booking": 30.0
  },
  "pagination": {
    "default_page": 1,
    "default_limit": 50,
    "max_limit": 100
  }
}
```

## Usage

The configuration is automatically loaded by the `Settings` class in `app/core/config.py`. You can access configuration values through the `settings` object:

```python
from app.core.config import settings

# Get default headers
headers = settings.get_default_headers(accept_language="es")

# Get endpoint URL with parameters
url = settings.get_endpoint_url('price_recommendation', 
                               hotel_id="123", 
                               api_token="token", 
                               recommendation_id="rec123")

# Access individual settings
api_key = settings.XENI_API_KEY
base_url = settings.XENI_BASE_URL
```

## Benefits

1. **No Rebuild Required**: Changes to API URLs, headers, or other settings can be made by editing the JSON file without rebuilding the application.

2. **Centralized Configuration**: All API settings are in one place, making it easy to manage different environments (dev, staging, production).

3. **Type Safety**: The Settings class provides type hints and validation for configuration values.

4. **Flexible Headers**: The `get_default_headers()` method allows for easy customization of headers while maintaining consistency.

5. **Environment-Specific**: You can easily create different JSON files for different environments and load them based on environment variables.

## Environment-Specific Configuration

To use different configurations for different environments, you can:

1. Create environment-specific JSON files (e.g., `api_config_prod.json`, `api_config_dev.json`)
2. Modify the `Settings` class to load the appropriate file based on an environment variable
3. Use environment variables to override specific values in the JSON configuration

## Required Headers

The following headers are automatically included in all API requests:
- `x-api-key`: API authentication key
- `accept-language`: Language preference for responses
- `content-type`: Set to "application/json" for POST requests

Additional headers can be added through the `additional_headers` parameter in the `get_default_headers()` method.
