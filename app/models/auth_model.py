"""
Authentication Models
Pydantic models for Xeni Authentication API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AuthRequest(BaseModel):
    """Request model for authentication token generation"""
    api_key: str = Field(..., description="API key for authentication")
    secret: str = Field(..., description="Secret key for authentication")
    timestamp: int = Field(..., description="Current timestamp")


class AuthResponse(BaseModel):
    """Response model for authentication token generation"""
    status: str = Field(..., description="Response status (success, error)")
    message: str = Field(..., description="Response message")
    signature: str = Field(..., description="Generated authentication signature")
    expiry: int = Field(..., description="Token expiry timestamp")
    timestamp: int = Field(..., description="Response timestamp")


class AuthErrorResponse(BaseModel):
    """Error response for authentication API"""
    status: str = Field(..., description="Error status")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code if available")




