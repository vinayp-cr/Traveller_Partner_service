"""
Message loader utility for externalizing hardcoded messages
"""
import json
import os
from pathlib import Path
from typing import Dict, Any
from app.core.logger import logger


class MessageLoader:
    """Loads and manages application messages from configuration files"""
    
    def __init__(self):
        self._messages = None
        self._load_messages()
    
    def _load_messages(self):
        """Load messages from the messages.json file"""
        try:
            config_file = os.getenv("MESSAGES_CONFIG_FILE", "messages.json")
            config_path = Path(__file__).parent.parent / "config" / config_file
            
            with open(config_path, "r", encoding="utf-8") as f:
                self._messages = json.load(f)
        except FileNotFoundError:
            # Fallback to default messages if file not found
            logger.warning("Messages config file not found, using default messages")
            self._messages = self._get_default_messages()
        except Exception as e:
            logger.warning(f"Could not load messages config: {e}")
            self._messages = self._get_default_messages()
    
    def _get_default_messages(self) -> Dict[str, Any]:
        """Fallback default messages if config file is not available"""
        return {
            "responses": {
                "success": {
                    "hotel_search_completed": "Hotel search completed successfully",
                    "hotel_booking_completed": "Hotel booking completed successfully"
                },
                "errors": {
                    "service_error": "Service error",
                    "hotelier_service_error": "Hotelier Service error"
                }
            },
            "service_info": {
                "name": "Hotel Integration API",
                "version": "1.0.0"
            },
            "health_check": {
                "status": "healthy",
                "service": "Hotel Integration API"
            }
        }
    
    def get_message(self, category: str, key: str, default: str = None) -> str:
        """
        Get a message by category and key
        
        Args:
            category: The message category (e.g., 'success', 'errors', 'info')
            key: The message key
            default: Default value if message not found
            
        Returns:
            The message string
        """
        try:
            return self._messages["responses"][category][key]
        except (KeyError, TypeError):
            return default or f"Message not found: {category}.{key}"
    
    def get_success_message(self, key: str, default: str = None) -> str:
        """Get a success message"""
        return self.get_message("success", key, default)
    
    def get_error_message(self, key: str, default: str = None) -> str:
        """Get an error message"""
        return self.get_message("errors", key, default)
    
    def get_info_message(self, key: str, default: str = None) -> str:
        """Get an info message"""
        return self.get_message("info", key, default)
    
    def get_service_info(self, key: str, default: str = None) -> str:
        """Get service information"""
        try:
            return self._messages["service_info"][key]
        except (KeyError, TypeError):
            return default or f"Service info not found: {key}"
    
    def get_health_info(self, key: str, default: str = None) -> str:
        """Get health check information"""
        try:
            return self._messages["health_check"][key]
        except (KeyError, TypeError):
            return default or f"Health info not found: {key}"
    
    def reload_messages(self):
        """Reload messages from the configuration file"""
        self._load_messages()


# Global message loader instance
message_loader = MessageLoader()
