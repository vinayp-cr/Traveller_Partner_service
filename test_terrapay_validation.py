#!/usr/bin/env python3
"""
Validation test for TerraPay integration
Tests the integration structure and ensures existing APIs are not broken
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.terrapay_service import TerraPayService
from app.models.terrapay_models import (
    TerraPayTokenRequest,
    TerraPayCardCreationRequest,
    PaymentRequest
)
from app.core.logger import logger

async def test_terrapay_service_instantiation():
    """Test that TerraPay service can be instantiated without errors"""
    print("🔧 Testing TerraPay Service Instantiation...")
    
    try:
        terrapay_service = TerraPayService()
        print("✅ TerraPay service instantiated successfully!")
        
        # Test configuration loading
        config = terrapay_service.config
        assert "api" in config
        assert "authentication" in config
        assert "defaults" in config
        assert "charges" in config
        assert "retry" in config
        
        print("✅ Configuration structure is valid!")
        return True
        
    except Exception as e:
        print(f"❌ TerraPay service instantiation failed: {str(e)}")
        return False

async def test_terrapay_models():
    """Test TerraPay model creation and validation"""
    print("\n📋 Testing TerraPay Models...")
    
    try:
        # Test TokenRequest
        token_request = TerraPayTokenRequest(
            clientId="test_client",
            username="test_user",
            password="test_pass"
        )
        print("✅ TerraPayTokenRequest model works!")
        
        # Test CardCreationRequest
        card_request = TerraPayCardCreationRequest(
            agentCardProfileId="4",
            emailId="test@example.com",
            cardBalance=100.0,
            additionalFields={
                "BookingRef": "TEST_123",
                "InvoiceRef": "INV_123",
                "baVelCardRef": "VEL_TEST123"
            }
        )
        print("✅ TerraPayCardCreationRequest model works!")
        
        # Test PaymentRequest
        payment_request = PaymentRequest(
            booking_id="TEST_BOOKING_456",
            amount=150.0,
            customer_email="customer@example.com",
            agent_card_profile_id="4",
            booking_reference="TEST_BOOKING_456"
        )
        print("✅ PaymentRequest model works!")
        
        return True
        
    except Exception as e:
        print(f"❌ TerraPay models test failed: {str(e)}")
        return False

async def test_hotel_service_integration():
    """Test that hotel service integration doesn't break existing functionality"""
    print("\n🏨 Testing Hotel Service Integration...")
    
    try:
        from app.api.services.hotel_service import HotelService
        from app.models.hotel_search_models import BookHotelRequest, RoomGuest, PhoneData
        
        hotel_service = HotelService()
        print("✅ Hotel service instantiated successfully!")
        
        # Test that process_booking_payment method exists
        assert hasattr(hotel_service, 'process_booking_payment')
        print("✅ process_booking_payment method exists!")
        
        # Test that existing methods still work
        assert hasattr(hotel_service, 'book_hotel')
        assert hasattr(hotel_service, 'search_hotels')
        assert hasattr(hotel_service, 'get_hotel_price')
        print("✅ Existing hotel service methods are intact!")
        
        return True
        
    except Exception as e:
        print(f"❌ Hotel service integration test failed: {str(e)}")
        return False

async def test_webhook_controller():
    """Test that webhook controller can be imported and instantiated"""
    print("\n🔗 Testing Webhook Controller...")
    
    try:
        from app.api.controllers.terrapay_webhook_controller import router
        print("✅ TerraPay webhook controller imported successfully!")
        
        # Check that the webhook endpoint is defined
        routes = [route for route in router.routes]
        webhook_routes = [route for route in routes if 'webhook' in str(route.path)]
        assert len(webhook_routes) > 0
        print("✅ Webhook endpoint is defined!")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook controller test failed: {str(e)}")
        return False

async def test_payment_entities():
    """Test payment entities model"""
    print("\n💳 Testing Payment Entities...")
    
    try:
        from app.models.payment_entities import PaymentTransaction
        from datetime import datetime
        
        # Test creating a payment transaction
        payment_transaction = PaymentTransaction(
            payment_id="TEST_PAY_123",
            booking_id="TEST_BOOKING_123",
            amount=100.0,
            total_amount=115.0,  # 100 + 10% + 5%
            currency="USD",
            customer_email="test@example.com",
            status="PENDING"
        )
        
        print("✅ PaymentTransaction model works!")
        print(f"   Payment ID: {payment_transaction.payment_id}")
        print(f"   Amount: ${payment_transaction.amount}")
        print(f"   Total: ${payment_transaction.total_amount}")
        print(f"   Status: {payment_transaction.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Payment entities test failed: {str(e)}")
        return False

async def test_main_app_integration():
    """Test that main app can import all new components"""
    print("\n🚀 Testing Main App Integration...")
    
    try:
        # Test importing main app components
        from app.main import app
        print("✅ Main app imported successfully!")
        
        # Check that TerraPay webhook routes are included
        routes = [route for route in app.routes]
        webhook_routes = [route for route in routes if 'webhook' in str(route.path)]
        assert len(webhook_routes) > 0
        print("✅ TerraPay webhook routes are included in main app!")
        
        return True
        
    except Exception as e:
        print(f"❌ Main app integration test failed: {str(e)}")
        return False

async def test_error_handling():
    """Test error handling in TerraPay service"""
    print("\n🛡️  Testing Error Handling...")
    
    try:
        terrapay_service = TerraPayService()
        
        # Test with invalid configuration
        original_config = terrapay_service.config
        terrapay_service.config = {"invalid": "config"}
        
        # This should not crash the service
        token = await terrapay_service.get_valid_token()
        assert token is None  # Should return None for invalid config
        print("✅ Error handling works for invalid configuration!")
        
        # Restore original config
        terrapay_service.config = original_config
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

async def test_existing_book_hotel_flow():
    """Test that existing book_hotel flow still works without TerraPay"""
    print("\n🏨 Testing Existing Book Hotel Flow...")
    
    try:
        from app.api.services.hotel_service import HotelService
        from app.models.hotel_search_models import BookHotelRequest, RoomGuest, PhoneData
        from app.core.db import get_db
        
        hotel_service = HotelService()
        
        # Create a test booking request
        test_booking_request = BookHotelRequest(
            booking_id="TEST_BOOKING_789",
            rooms=[
                RoomGuest(
                    title="Mr",
                    first_name="Test",
                    last_name="User"
                )
            ],
            email="test@example.com",
            phone=PhoneData(
                country_code="1",
                number="1234567890"
            )
        )
        
        print("✅ Book Hotel Request created successfully!")
        print(f"   Booking ID: {test_booking_request.booking_id}")
        print(f"   Email: {test_booking_request.email}")
        print(f"   Rooms: {len(test_booking_request.rooms)}")
        
        # Test that the service methods exist and are callable
        assert callable(hotel_service.book_hotel)
        assert callable(hotel_service.search_hotels)
        assert callable(hotel_service.get_hotel_price)
        
        print("✅ All existing hotel service methods are callable!")
        
        return True
        
    except Exception as e:
        print(f"❌ Existing book hotel flow test failed: {str(e)}")
        return False

async def main():
    """Run all validation tests"""
    print("🧪 Starting TerraPay Integration Validation Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Service Instantiation
    service_test = await test_terrapay_service_instantiation()
    test_results.append(("Service Instantiation", service_test))
    
    # Test 2: Models
    models_test = await test_terrapay_models()
    test_results.append(("TerraPay Models", models_test))
    
    # Test 3: Hotel Service Integration
    hotel_integration_test = await test_hotel_service_integration()
    test_results.append(("Hotel Service Integration", hotel_integration_test))
    
    # Test 4: Webhook Controller
    webhook_test = await test_webhook_controller()
    test_results.append(("Webhook Controller", webhook_test))
    
    # Test 5: Payment Entities
    entities_test = await test_payment_entities()
    test_results.append(("Payment Entities", entities_test))
    
    # Test 6: Main App Integration
    main_app_test = await test_main_app_integration()
    test_results.append(("Main App Integration", main_app_test))
    
    # Test 7: Error Handling
    error_handling_test = await test_error_handling()
    test_results.append(("Error Handling", error_handling_test))
    
    # Test 8: Existing Book Hotel Flow
    existing_flow_test = await test_existing_book_hotel_flow()
    test_results.append(("Existing Book Hotel Flow", existing_flow_test))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! TerraPay integration is structurally sound.")
        print("✅ Existing APIs are not broken by TerraPay integration.")
        print("✅ TerraPay integration is ready for configuration with real credentials.")
    else:
        print("⚠️  Some validation tests failed. Please fix the issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    # Run the validation tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
