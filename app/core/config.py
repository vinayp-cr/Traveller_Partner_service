import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # Load JSON configuration based on environment
        config_file = os.getenv("API_CONFIG_FILE", "api_config_prod.json")
        config_path = Path(__file__).parent.parent / "config" / config_file
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # API URLs
        self.XENI_BASE_URL = self.config["api"]["base_url"]
        self.XENI_AUTOCOMPLETE_API_URL = f"{self.XENI_BASE_URL}{self.config['api']['endpoints']['autosuggest']}"
        self.XENI_HOTEL_SEARCH_API_URL = f"{self.XENI_BASE_URL}{self.config['api']['endpoints']['hotel_search']}"
        
        # Headers
        self.XENI_API_KEY = self.config["headers"]["default"]["x-api-key"]
        self.DEFAULT_ACCEPT_LANGUAGE = self.config["headers"]["default"]["accept-language"]
        self.DEFAULT_CONTENT_TYPE = self.config["headers"]["default"]["content-type"]
        
        # Timeouts
        self.DEFAULT_TIMEOUT = self.config["timeouts"]["default"]
        self.BOOKING_TIMEOUT = self.config["timeouts"]["booking"]
        
        # Pagination
        self.DEFAULT_PAGE = self.config["pagination"]["default_page"]
        self.DEFAULT_LIMIT = self.config["pagination"]["default_limit"]
        self.MAX_LIMIT = self.config["pagination"]["max_limit"]
        
        # Required headers
        self.REQUIRED_HEADERS = self.config["headers"]["required_headers"]
    
    def get_default_headers(self, accept_language: str = None, additional_headers: dict = None):
        """Get default headers with optional overrides"""
        headers = {
            "x-api-key": self.XENI_API_KEY,
            "accept-language": accept_language or self.DEFAULT_ACCEPT_LANGUAGE,
            "content-type": self.DEFAULT_CONTENT_TYPE
        }
        
        if additional_headers:
            headers.update(additional_headers)
            
        return headers
    
    def get_endpoint_url(self, endpoint_name: str, **kwargs):
        """Get full URL for an endpoint with optional parameter substitution"""
        endpoint = self.config["api"]["endpoints"][endpoint_name]
        if kwargs:
            return f"{self.XENI_BASE_URL}{endpoint.format(**kwargs)}"
        return f"{self.XENI_BASE_URL}{endpoint}"

settings = Settings()

