"""
Authentication Service
Service for generating and managing Xeni authentication tokens.
"""

import httpx
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.logger import logger
import os
import json
from pathlib import Path

def load_config():
    config_file = os.getenv("API_CONFIG_FILE", "api_config.json")
    config_path = Path(__file__).parent.parent / "config" / config_file
    with open(config_path, 'r') as f:
        return json.load(f)
from app.models.auth_model import AuthRequest, AuthResponse, AuthErrorResponse


class AuthService:
    """Service for handling Xeni authentication token generation and caching"""
    
    def __init__(self):
        self.config = load_config()
        self.auth_config = self.config.get('auth', {})
        self.base_url = self.config['api']['base_url']
        self._token_cache = {}
    
    async def generate_auth_token(self) -> Dict[str, Any]:
        """
        Generate authentication token from Xeni API
        
        Returns:
            Dict containing authentication response with signature
        """
        try:
            # Check if we have a valid cached token
            cached_token = self._get_cached_token()
            if cached_token:
                logger.info("Using cached authentication token")
                return cached_token
            
            # Generate new token
            logger.info("Generating new authentication token")
            
            # Create request payload
            current_timestamp = int(time.time())
            auth_request = AuthRequest(
                api_key=self.auth_config.get('api_key'),
                secret=self.auth_config.get('secret_key'),
                timestamp=current_timestamp
            )
            
            # Make API call
            url = f"{self.base_url}{self.config['api']['endpoints']['auth_generate']}"
            headers = {
                "content-type": "application/json",
                "accept": "application/json"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=auth_request.model_dump(), headers=headers)
                
                if response.status_code == 200:
                    auth_data = response.json()
                    
                    # Validate response
                    if auth_data.get('status') == 'success':
                        # Cache the token
                        self._cache_token(auth_data)
                        
                        logger.info(f"Authentication token generated successfully - Expiry: {auth_data.get('expiry')}")
                        return auth_data
                    else:
                        error_msg = f"Authentication failed: {auth_data.get('message', 'Unknown error')}"
                        logger.error(error_msg)
                        return {
                            "status": "error",
                            "message": error_msg,
                            "error_code": "auth_failed"
                        }
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Authentication API error: {error_msg}")
                    return {
                        "status": "error",
                        "message": error_msg,
                        "error_code": f"http_{response.status_code}"
                    }
                    
        except Exception as e:
            error_msg = f"Authentication service error: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "message": error_msg,
                "error_code": "service_error"
            }
    
    def _get_cached_token(self) -> Optional[Dict[str, Any]]:
        """Get cached token if still valid"""
        if 'token' in self._token_cache and 'expiry' in self._token_cache:
            current_time = int(time.time())
            if current_time < self._token_cache['expiry'] - 300:  # 5 minutes buffer
                return self._token_cache['token']
            else:
                # Token expired, clear cache
                self._token_cache.clear()
        return None
    
    def _cache_token(self, token_data: Dict[str, Any]) -> None:
        """Cache the authentication token"""
        self._token_cache = {
            'token': token_data,
            'expiry': token_data.get('expiry', int(time.time()) + 3600)
        }
        logger.info(f"Authentication token cached until {token_data.get('expiry')}")
    
    async def get_valid_auth_token(self) -> Optional[str]:
        """
        Get a valid authentication signature for API calls
        
        Returns:
            Authentication signature string or None if failed
        """
        try:
            auth_response = await self.generate_auth_token()
            
            if auth_response.get('status') == 'success':
                return auth_response.get('signature')
            else:
                logger.error(f"Failed to get valid auth token: {auth_response.get('message')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting valid auth token: {str(e)}")
            return None
    
    def clear_token_cache(self) -> None:
        """Clear the token cache"""
        self._token_cache.clear()
        logger.info("Authentication token cache cleared")
