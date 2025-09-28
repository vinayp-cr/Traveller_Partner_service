from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class TerraPayTokenRequest(BaseModel):
    """TerraPay token generation request model"""
    clientId: str = Field(..., description="TerraPay client ID")
    username: str = Field(..., description="TerraPay username")
    password: str = Field(..., description="TerraPay password")

class TerraPayTokenResponse(BaseModel):
    """TerraPay token generation response model"""
    success: bool
    token: Optional[str] = None
    message: str
    expires_in: Optional[int] = None
    token_type: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

class TerraPayCardCreationRequest(BaseModel):
    """TerraPay card creation request model"""
    agentCardProfileId: str = Field(..., description="Agent card profile ID")
    cardAccountType: str = Field(default="PrepaidPayout", description="Card account type")
    emailId: str = Field(..., description="Customer email")
    cardBalance: float = Field(..., description="Card balance amount")
    cardCurrency: str = Field(default="USD", description="Card currency")
    internationalTxnSupported: bool = Field(default=True, description="International transaction support")
    additionalFields: Dict[str, str] = Field(..., description="Additional fields including BookingRef")
    cardRecipientEmailId: Optional[str] = Field(None, description="Card recipient email")
    cardRecipientName: Optional[str] = Field(None, description="Card recipient name")

class TerraPayCardCreationResponse(BaseModel):
    """TerraPay card creation response model"""
    success: bool
    message: str
    errorCode: Optional[str] = None
    traceID: Optional[str] = None
    encryptedPayload: Optional[str] = None
    refNo: Optional[str] = None
    cardUID: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Decrypted payload fields (not stored in DB for PCI compliance)
    cardNumber: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    maskedCardNumber: Optional[str] = None
    cvv: Optional[str] = None
    availableBalance: Optional[float] = None
    expirationDate: Optional[str] = None
    cardStatus: Optional[str] = None
    currency: Optional[str] = None
    
    # Additional fields
    additionalFields: Optional[Dict[str, str]] = None
    created_at: Optional[str] = None

class PaymentRequest(BaseModel):
    """Payment request for booking integration"""
    booking_id: str = Field(..., description="Xeni booking ID")
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(default="USD", description="Payment currency")
    customer_email: str = Field(..., description="Customer email")
    agent_card_profile_id: str = Field(..., description="Agent card profile ID")
    booking_reference: str = Field(..., description="Booking reference")
    additional_restrictions: Optional[Dict[str, Any]] = Field(None, description="Additional restrictions")

class PaymentResponse(BaseModel):
    """Payment response model"""
    success: bool
    payment_id: str
    message: str
    terrapay_response: Optional[TerraPayCardCreationResponse] = None
    error_details: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3

class TerraPayWebhookPayload(BaseModel):
    """TerraPay webhook payload model"""
    eventType: str = Field(..., description="Webhook event type")
    cardId: str = Field(..., description="Card ID")
    traceID: str = Field(..., description="Trace ID")
    timestamp: str = Field(..., description="Event timestamp")
    data: Dict[str, Any] = Field(..., description="Event data")
