"""
Autosuggest Models
Consolidated Pydantic models for Xeni Autosuggest API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Union


class AutocompleteRequest(BaseModel):
    """Request model for autosuggest API"""
    key: str = Field(..., description="Search query text for autosuggest", min_length=1)


class LocationData(BaseModel):
    """Location coordinates data"""
    lat: float = Field(..., description="Latitude coordinate")
    long: float = Field(..., description="Longitude coordinate")


class AutosuggestItem(BaseModel):
    """Individual autosuggest item"""
    id: str = Field(..., description="Unique identifier for the location")
    country: str = Field(..., description="Country name")
    full_name: str = Field(..., description="Full location name including country")
    location: LocationData = Field(..., description="Location coordinates")
    name: str = Field(..., description="Location name")
    state: str = Field(..., description="State or province name")
    type: str = Field(..., description="Type of location (city, multicity, etc.)")


# Error Response Models
class ErrorField(BaseModel):
    """Error field information"""
    name: str = Field(..., description="Field name that caused the error")
    type: str = Field(..., description="Field type (query, body, etc.)")


class ErrorDescription(BaseModel):
    """Error description details"""
    type: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="Error message")
    fields: Optional[List[ErrorField]] = Field(None, description="Fields that caused the error")


class AutosuggestErrorResponse(BaseModel):
    """Error response for autosuggest API (400, 404, 500)"""
    desc: List[ErrorDescription] = Field(..., description="List of error descriptions")
    error: str = Field(..., description="Main error message")
    status: str = Field(..., description="Error status (failed)")
    correlation_id: Optional[str] = Field(None, description="X-Correlation-Id from response headers")


class AutosuggestSuccessResponse(BaseModel):
    """Success response for autosuggest API (200)"""
    status: str = Field(..., description="Response status (success)")
    message: str = Field(..., description="Response message")
    data: List[AutosuggestItem] = Field(..., description="List of autosuggest suggestions")
    correlation_id: Optional[str] = Field(None, description="X-Correlation-Id from response headers")


# Union type for all possible responses
AutosuggestResponse = Union[AutosuggestSuccessResponse, AutosuggestErrorResponse]
