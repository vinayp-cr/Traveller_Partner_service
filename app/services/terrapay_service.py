import os
import json
import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.logger import logger
from app.models.terrapay_models import (
    TerraPayTokenRequest,
    TerraPayTokenResponse,
    TerraPayCardCreationRequest, 
    TerraPayCardCreationResponse,
    TerraPayWebhookPayload,
    PaymentRequest,
    PaymentResponse
)
from app.utilities.message_loader import message_loader


class TerraPayService:
    """Service for TerraPay API integration"""
    
    def __init__(self):
        self.base_url = "https://uat-ipservice.terrapay.com/prepaidservices/rest"
        self.token_endpoint = "/setupServices/setupService/generatePartnerToken"
        self.create_card_endpoint = "/cardManagementServices/cardManagementService/createCustomerAccountAndCard"
        self.timeout = 30.0
        
        # Load TerraPay configuration
        self.config = self._load_terrapay_config()
        
        # Token management
        self._cached_token = None
        self._token_expires_at = None
    
    def _load_terrapay_config(self) -> Dict[str, Any]:
        """Load TerraPay configuration from config file"""
        try:
            config_path = "app/config/terrapay_config.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Failed to load TerraPay config: {str(e)}")
            # Fallback to environment variables
            return {
                "api": {
                    "base_url": "https://uat-ipservice.terrapay.com/prepaidservices/rest",
                    "timeout": 30.0
                },
                "authentication": {
                    "clientId": os.getenv("TERRAPAY_CLIENT_ID", ""),
                    "username": os.getenv("TERRAPAY_USERNAME", ""),
                    "password": os.getenv("TERRAPAY_PASSWORD", "")
                },
                "defaults": {
                    "agent_card_profile_id": "4",
                    "currency": "USD"
                },
                "charges": {
                    "service_charge_percentage": 10.0,
                    "additional_charge_percentage": 5.0
                },
                "retry": {
                    "max_retries": 3,
                    "retry_delay_seconds": 5
                }
            }
    
    async def generate_token(self) -> TerraPayTokenResponse:
        """
        Generate TerraPay authentication token.
        
        Returns:
            TerraPay token response
        """
        try:
            logger.info("Generating TerraPay authentication token")
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "clientId": self.config["authentication"]["clientId"]
            }
            
            # Prepare request payload
            token_request = TerraPayTokenRequest(
                clientId=self.config["authentication"]["clientId"],
                username=self.config["authentication"]["username"],
                password=self.config["authentication"]["password"]
            )
            
            payload = token_request.model_dump()
            
            # Make API call
            url = f"{self.config['api']['base_url']}{self.token_endpoint}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                logger.info(f"TerraPay token API response status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        token = response_data.get("token") or response_data.get("access_token")
                        
                        if token:
                            # Cache token with expiration (default 1 hour)
                            self._cached_token = token
                            expires_in = response_data.get("expires_in", 3600)
                            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                            
                            logger.info("TerraPay token generated successfully")
                            return TerraPayTokenResponse(
                                success=True,
                                token=token,
                                message="Token generated successfully",
                                expires_in=expires_in,
                                token_type=response_data.get("token_type", "Bearer")
                            )
                        else:
                            return TerraPayTokenResponse(
                                success=False,
                                message="No token found in response",
                                error_details=response_data
                            )
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse TerraPay token response JSON: {str(e)}")
                        return TerraPayTokenResponse(
                            success=False,
                            message="Invalid response format from TerraPay token API",
                            error_details={"error": str(e)}
                        )
                else:
                    try:
                        error_data = response.json()
                        error_message = error_data.get("message", f"TerraPay token API error: {response.status_code}")
                    except:
                        error_message = f"TerraPay token API error: {response.status_code} - {response.text}"
                    
                    logger.error(f"TerraPay token API error: {error_message}")
                    return TerraPayTokenResponse(
                        success=False,
                        message=error_message,
                        error_details={"status_code": response.status_code, "response": response.text}
                    )
                    
        except httpx.RequestError as e:
            error_msg = f"TerraPay token API request error: {str(e)}"
            logger.error(error_msg)
            return TerraPayTokenResponse(success=False, message=error_msg)
        except Exception as e:
            error_msg = f"TerraPay token service error: {str(e)}"
            logger.error(error_msg)
            return TerraPayTokenResponse(success=False, message=error_msg)
    
    async def get_valid_token(self) -> Optional[str]:
        """
        Get a valid TerraPay token, generating a new one if needed.
        
        Returns:
            Valid token string or None if failed
        """
        try:
            # Check if we have a valid cached token
            if (self._cached_token and 
                self._token_expires_at and 
                datetime.utcnow() < self._token_expires_at - timedelta(minutes=5)):  # 5 min buffer
                return self._cached_token
            
            # Generate new token
            token_response = await self.generate_token()
            if token_response.success:
                return token_response.token
            else:
                logger.error(f"Failed to generate TerraPay token: {token_response.message}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting valid TerraPay token: {str(e)}")
            return None
    
    async def create_card_and_fund(self, request: TerraPayCardCreationRequest) -> TerraPayCardCreationResponse:
        """
        Create a card and fund it through TerraPay API
        
        Args:
            request: TerraPay card creation request
            
        Returns:
            TerraPay card creation response
        """
        try:
            logger.info(f"Creating TerraPay card for email: {request.emailId}")
            
            # Get valid authentication token
            token = await self.get_valid_token()
            if not token:
                return TerraPayCardCreationResponse(
                    success=False,
                    message="Failed to obtain TerraPay authentication token"
                )
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
                "clientId": self.config["authentication"]["clientId"]
            }
            
            # Prepare request payload
            payload = request.model_dump(exclude_none=True)
            
            # Make API call
            url = f"{self.config['api']['base_url']}{self.create_card_endpoint}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                logger.info(f"TerraPay API response status: {response.status_code}")
                logger.info(f"TerraPay API response: {response.text}")
                
                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        return self._parse_success_response(response_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse TerraPay response JSON: {str(e)}")
                        raise HTTPException(
                            status_code=500, 
                            detail="Invalid response format from TerraPay API"
                        )
                else:
                    return self._parse_error_response(response)
                    
        except httpx.RequestError as e:
            error_msg = f"TerraPay API request error: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        except Exception as e:
            error_msg = f"TerraPay service error: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
    
    def _parse_success_response(self, response_data: Dict[str, Any]) -> TerraPayCardCreationResponse:
        """Parse successful TerraPay API response"""
        try:
            # Extract card details from response
            data = response_data.get("data", {})
            
            return TerraPayCardCreationResponse(
                success=True,
                message=response_data.get("message", "Card created successfully"),
                data=response_data,
                cardId=data.get("cardId"),
                cardNumber=data.get("cardNumber"),
                expiryDate=data.get("expiryDate"),
                cvv=data.get("cvv"),
                cardStatus=data.get("cardStatus", "ACTIVE"),
                balance=data.get("balance"),
                currency=data.get("currency"),
                created_at=datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error(f"Error parsing TerraPay success response: {str(e)}")
            return TerraPayCardCreationResponse(
                success=True,
                message="Card created successfully",
                data=response_data,
                created_at=datetime.utcnow().isoformat()
            )
    
    def _parse_error_response(self, response: httpx.Response) -> TerraPayCardCreationResponse:
        """Parse error response from TerraPay API"""
        try:
            error_data = response.json()
            error_message = error_data.get("message", f"TerraPay API error: {response.status_code}")
        except:
            error_message = f"TerraPay API error: {response.status_code} - {response.text}"
        
        logger.error(f"TerraPay API error: {error_message}")
        
        return TerraPayCardCreationResponse(
            success=False,
            message=error_message,
            data={"status_code": response.status_code, "response": response.text},
            created_at=datetime.utcnow().isoformat()
        )
    
    async def process_booking_payment(self, payment_request: PaymentRequest, db: Session = None) -> PaymentResponse:
        """
        Process payment for a booking by creating a TerraPay card
        
        Args:
            payment_request: Payment request with booking details
            db: Database session for saving payment transaction
            
        Returns:
            Payment response with TerraPay card details
        """
        try:
            logger.info(f"Processing payment for booking: {payment_request.booking_id}")
            
            # Create TerraPay card creation request
            terrapay_request = TerraPayCardCreationRequest(
                emailId=payment_request.customer_email,
                cardBalance=payment_request.amount,
                cardCurrency=payment_request.currency,
                agentCardProfileId=payment_request.agent_card_profile_id,
                cardAccountType="PrepaidPayout",
                internationalTxnSupported=True,
                additionalFields={
                    "BookingRef": payment_request.booking_reference,
                    "InvoiceRef": "",
                    "baVelCardRef": f"VEL{payment_request.booking_id[:8].upper()}"
                }
            )
            
            # Add additional restrictions if provided
            if payment_request.additional_restrictions:
                if "maxDailyAmount" in payment_request.additional_restrictions:
                    terrapay_request.maxDailyAmount = payment_request.additional_restrictions["maxDailyAmount"]
                if "maxDailyCount" in payment_request.additional_restrictions:
                    terrapay_request.maxDailyCount = payment_request.additional_restrictions["maxDailyCount"]
                if "singleCardUse" in payment_request.additional_restrictions:
                    terrapay_request.singleCardUse = payment_request.additional_restrictions["singleCardUse"]
            
            # Create card and fund it
            terrapay_response = await self.create_card_and_fund(terrapay_request)
            
            # Generate payment ID
            payment_id = f"PAY_{payment_request.booking_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create payment response
            payment_response = PaymentResponse(
                success=terrapay_response.success,
                payment_id=payment_id,
                message="Payment processed successfully" if terrapay_response.success else terrapay_response.message,
                terrapay_response=terrapay_response if terrapay_response.success else None,
                error_details={"terrapay_error": terrapay_response.data} if not terrapay_response.success else None
            )
            
            # Save payment transaction to database if available
            if db:
                try:
                    self.payment_repository.save_payment_transaction(db, payment_request, payment_response)
                    logger.info(f"Payment transaction saved to database: {payment_id}")
                except Exception as db_error:
                    logger.error(f"Failed to save payment transaction to database: {str(db_error)}")
                    # Don't fail the payment if database save fails
            
            return payment_response
                
        except Exception as e:
            error_msg = f"Payment processing error: {str(e)}"
            logger.error(error_msg)
            return PaymentResponse(
                success=False,
                payment_id=f"PAY_{payment_request.booking_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                message=error_msg,
                error_details={"error": str(e)}
            )
    
    async def process_booking_payment_with_retry(
        self, 
        payment_request: PaymentRequest, 
        payment_transaction, 
        db: Session
    ) -> PaymentResponse:
        """
        Process payment with retry logic and webhook support.
        """
        max_retries = self.config["retry"]["max_retries"]
        
        for attempt in range(max_retries + 1):
            try:
                # Update retry count
                payment_transaction.retry_count = attempt
                payment_transaction.last_retry_at = datetime.utcnow()
                
                if attempt > 0:
                    payment_transaction.status = "RETRYING"
                    db.commit()
                    logger.info(f"Retrying payment for booking {payment_request.booking_id}, attempt {attempt}")
                
                # Process payment
                payment_result = await self.process_booking_payment(payment_request, db)
                
                if payment_result.success:
                    # Update transaction status
                    payment_transaction.status = "SUCCESS"
                    if payment_result.terrapay_response:
                        payment_transaction.terrapay_trace_id = payment_result.terrapay_response.traceID
                        payment_transaction.terrapay_ref_no = payment_result.terrapay_response.refNo
                        payment_transaction.terrapay_card_uid = payment_result.terrapay_response.cardUID
                    payment_transaction.completed_at = datetime.utcnow()
                    db.commit()
                    
                    logger.info(f"Payment successful for booking {payment_request.booking_id}")
                    return payment_result
                else:
                    # Log error and retry if attempts remaining
                    payment_transaction.error_message = payment_result.message
                    if attempt < max_retries:
                        logger.warning(f"Payment failed for booking {payment_request.booking_id}, retrying...")
                        await asyncio.sleep(self.config["retry"]["retry_delay_seconds"])
                        continue
                    else:
                        payment_transaction.status = "FAILED"
                        db.commit()
                        logger.error(f"Payment failed for booking {payment_request.booking_id} after {max_retries} retries")
                        return payment_result
                        
            except Exception as e:
                payment_transaction.error_message = str(e)
                if attempt < max_retries:
                    logger.warning(f"Payment error for booking {payment_request.booking_id}, retrying: {str(e)}")
                    await asyncio.sleep(self.config["retry"]["retry_delay_seconds"])
                    continue
                else:
                    payment_transaction.status = "FAILED"
                    db.commit()
                    logger.error(f"Payment error for booking {payment_request.booking_id} after {max_retries} retries: {str(e)}")
                    return PaymentResponse(
                        success=False,
                        payment_id=payment_transaction.payment_id,
                        message=str(e),
                        error_details={"error": str(e)},
                        retry_count=attempt,
                        max_retries=max_retries
                    )
    
    async def handle_webhook(self, webhook_payload: TerraPayWebhookPayload, db: Session) -> Dict[str, Any]:
        """
        Handle TerraPay webhook notifications with database updates.
        
        Args:
            webhook_payload: Webhook payload from TerraPay
            db: Database session
            
        Returns:
            Processing result
        """
        try:
            logger.info(f"Processing TerraPay webhook: {webhook_payload.eventType} for card: {webhook_payload.cardId}")
            
            # Find payment transaction by trace ID or card UID
            from app.models.payment_entities import PaymentTransaction
            
            payment_transaction = db.query(PaymentTransaction).filter(
                PaymentTransaction.terrapay_trace_id == webhook_payload.traceID
            ).first()
            
            if not payment_transaction:
                logger.warning(f"No payment transaction found for webhook trace ID: {webhook_payload.traceID}")
                return {"status": "ignored", "reason": "Transaction not found"}
            
            # Update webhook status
            payment_transaction.webhook_received = True
            if not payment_transaction.webhook_events:
                payment_transaction.webhook_events = []
            
            payment_transaction.webhook_events.append({
                "event_type": webhook_payload.eventType,
                "timestamp": webhook_payload.timestamp,
                "data": webhook_payload.data
            })
            
            # Process different webhook event types
            if webhook_payload.eventType == "CARD_CREATED":
                payment_transaction.status = "SUCCESS"
                logger.info(f"Card created webhook processed for payment: {payment_transaction.payment_id}")
            elif webhook_payload.eventType == "CARD_FUNDED":
                logger.info(f"Card funded webhook processed for payment: {payment_transaction.payment_id}")
            elif webhook_payload.eventType == "TRANSACTION_COMPLETED":
                payment_transaction.completed_at = datetime.utcnow()
                logger.info(f"Transaction completed webhook processed for payment: {payment_transaction.payment_id}")
            elif webhook_payload.eventType == "CARD_DEACTIVATED":
                payment_transaction.status = "FAILED"
                logger.info(f"Card deactivated webhook processed for payment: {payment_transaction.payment_id}")
            else:
                logger.warning(f"Unknown webhook event type: {webhook_payload.eventType}")
                return {"status": "ignored", "reason": "Unknown event type"}
            
            db.commit()
            return {"status": "processed", "event": webhook_payload.eventType}
                
        except Exception as e:
            error_msg = f"Webhook processing error: {str(e)}"
            logger.error(error_msg)
            return {"status": "error", "message": error_msg}
    
    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Validate TerraPay webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature
            
        Returns:
            True if signature is valid
        """
        try:
            import hmac
            import hashlib
            
            webhook_secret = self.config.get("webhook", {}).get("secret_key", "")
            if not webhook_secret:
                logger.warning("No webhook secret configured, skipping signature validation")
                return True
            
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Webhook signature validation error: {str(e)}")
            return False
