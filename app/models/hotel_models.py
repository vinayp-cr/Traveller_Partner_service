from pydantic import BaseModel
from typing import Optional, Any

class HotelRequest(BaseModel):
    city: str
    check_in: str
    check_out: str
    adults: int
    children: int = 0

class HotelResponse(BaseModel):
    id: int
    hotel_id: str
    name: str
    city: Optional[str]
    country: Optional[str]
    rating: Optional[float]
    latitude: Optional[float]
    longitude: Optional[float]
    raw_response: Any


