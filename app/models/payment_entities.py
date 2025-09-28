from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class PaymentTransaction(Base):
    """Payment transaction model - PCI compliant (no card details stored)"""
    __tablename__ = "payment_transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(String(255), unique=True, index=True)
    booking_id = Column(String(255), index=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    service_charge = Column(Float, default=0.0)
    additional_charge = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # TerraPay references (no sensitive data)
    terrapay_trace_id = Column(String(255), nullable=True)
    terrapay_ref_no = Column(String(255), nullable=True)
    terrapay_card_uid = Column(String(255), nullable=True)
    
    # Status tracking
    status = Column(String(50), default="PENDING")  # PENDING, SUCCESS, FAILED, RETRYING
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Customer info
    customer_email = Column(String(255), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    last_retry_at = Column(DateTime, nullable=True)
    
    # Webhook tracking
    webhook_received = Column(Boolean, default=False)
    webhook_events = Column(JSON, nullable=True)  # Store webhook event history
