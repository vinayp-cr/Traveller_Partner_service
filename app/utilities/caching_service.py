import requests
import json 
from datetime import datetime
import os
from pathlib import Path
from app.core.logger import logger

# Optional memcache import
try:
    import memcache
    MEMCACHE_AVAILABLE = True
except ImportError:
    MEMCACHE_AVAILABLE = False
    logger.warning("Memcache not available - caching will be disabled")

# Load JSON configuration
def load_config():
    config_file = os.getenv("API_CONFIG_FILE", "api_config.json")
    config_path = Path(__file__).parent.parent / "config" / config_file
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()

# Connect to Memcached (if available)
if MEMCACHE_AVAILABLE:
    try:
        mc = memcache.Client(['127.0.0.1:11211'])
        logger.info("Memcache client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize memcache client: {e}")
        mc = None
else:
    mc = None

## fimctionality for Polling mechanism:  repeatedly calls an API at fixed intervals
def get_hotel_availability(hotel_id, checkin, checkout):
    if not MEMCACHE_AVAILABLE or mc is None:
        logger.info("Cache not available, calling API directly for hotel availability")
        url = config["api"]["endpoints"]["Check_availability"]
        response = requests.get(url, params={"checkin": checkin, "checkout": checkout})
        return response.json()
    
    cache_key = f"hotel:{hotel_id}:{checkin}:{checkout}"
    cached_data = mc.get(cache_key)

    if cached_data:
        logger.info("Cache hit for hotel availability")
        return json.loads(cached_data)

    logger.info("Cache miss, calling API for hotel availability")
    url = config["api"]["endpoints"]["Check_availability"]
    response = requests.get(url, params={"checkin": checkin, "checkout": checkout})
    data = response.json()

    # Store in cache for 5 minutes
    mc.set(cache_key, json.dumps(data), time=300)

    return data