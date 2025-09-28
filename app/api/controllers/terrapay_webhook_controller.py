from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.terrapay_models import TerraPayWebhookPayload
from app.services.terrapay_service import TerraPayService
from app.core.db import get_db
from app.core.logger import logger
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/webhook/terrapay")
async def handle_terrapay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle TerraPay webhook notifications.
    """
    try:
        # Get raw payload
        payload = await request.body()
        
        # Parse webhook payload
        webhook_data = await request.json()
        webhook_payload = TerraPayWebhookPayload(**webhook_data)
        
        # Validate webhook signature (implement based on TerraPay requirements)
        terrapay_service = TerraPayService()
        # signature = request.headers.get("X-TerraPay-Signature")
        # if not terrapay_service.validate_webhook_signature(payload.decode(), signature):
        #     raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Process webhook
        result = await terrapay_service.handle_webhook(webhook_payload, db)
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
