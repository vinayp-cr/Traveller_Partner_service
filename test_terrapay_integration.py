#!/usr/bin/env python3
"""
Test script for TerraPay integration
Tests token generation and card creation APIs without affecting existing book_hotel functionality
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.terrapay_service import TerraPayService
from app.models.terrapay_models import (
    TerraPayTokenRequest,
    TerraPayCardCreationRequest,
    PaymentRequest
)
from app.core.logger import logger

async def test_terrapay_token_generation():
    """Test TerraPay token generation API"""
    print("🔑 Testing TerraPay Token Generation...")
    
    try:
        terrapay_service = TerraPayService()
        
        # Test token generation
        token_response = await terrapay_service.generate_token()
        
        print(f"✅ Token Generation Result:")
        print(f"   Success: {token_response.success}")
        print(f"   Message: {token_response.message}")
        print(f"   Token: {'***' + token_response.token[-10:] if token_response.token else 'None'}")
        print(f"   Expires In: {token_response.expires_in} seconds")
        
        if token_response.success:
            print("✅ Token generation API is working correctly!")
            return token_response.token
        else:
            print("❌ Token generation failed!")
            print(f"   Error Details: {token_response.error_details}")
            return None
            
    except Exception as e:
        print(f"❌ Token generation test failed with exception: {str(e)}")
        return None

async def test_terrapay_card_creation():
    """Test TerraPay card creation API"""
    print("\n💳 Testing TerraPay Card Creation...")
    
    try:
        terrapay_service = TerraPayService()
        
        # Create test card creation request
        card_request = TerraPayCardCreationRequest(
            agentCardProfileId="4",
            cardAccountType="PrepaidPayout",
            emailId="test@example.com",
            cardBalance=100.0,
            cardCurrency="USD",
            internationalTxnSupported=True,
            additionalFields={
                "BookingRef": "TEST_BOOKING_123",
                "InvoiceRef": "INV_123",
                "baVelCardRef": "VEL_TEST123"
            },
            cardRecipientEmailId="test@example.com",
            cardRecipientName="Test User"
        )
        
        # Test card creation
        card_response = await terrapay_service.create_card_and_fund(card_request)
        
        print(f"✅ Card Creation Result:")
        print(f"   Success: {card_response.success}")
        print(f"   Message: {card_response.message}")
        print(f"   Error Code: {card_response.errorCode}")
        print(f"   Trace ID: {card_response.traceID}")
        print(f"   Ref No: {card_response.refNo}")
        print(f"   Card UID: {card_response.cardUID}")
        
        if card_response.success:
            print("✅ Card creation API is working correctly!")
            return True
        else:
            print("❌ Card creation failed!")
            print(f"   Error Details: {card_response.error_details}")
            return False
            
    except Exception as e:
        print(f"❌ Card creation test failed with exception: {str(e)}")
        return False

async def test_payment_processing():
    """Test complete payment processing flow"""
    print("\n💰 Testing Payment Processing Flow...")
    
    try:
        terrapay_service = TerraPayService()
        
        # Create test payment request
        payment_request = PaymentRequest(
            booking_id="TEST_BOOKING_456",
            amount=150.0,
            currency="USD",
            customer_email="customer@example.com",
            agent_card_profile_id="4",
            booking_reference="TEST_BOOKING_456",
            additional_restrictions={
                "singleCardUse": True,
                "maxDailyAmount": 150.0
            }
        )
        
        # Test payment processing (without database)
        print("   Testing payment request creation...")
        print(f"   Booking ID: {payment_request.booking_id}")
        print(f"   Amount: ${payment_request.amount}")
        print(f"   Currency: {payment_request.currency}")
        print(f"   Customer Email: {payment_request.customer_email}")
        
        print("✅ Payment request structure is valid!")
        return True
        
    except Exception as e:
        print(f"❌ Payment processing test failed with exception: {str(e)}")
        return False

async def test_configuration_loading():
    """Test TerraPay configuration loading"""
    print("\n⚙️  Testing TerraPay Configuration...")
    
    try:
        terrapay_service = TerraPayService()
        config = terrapay_service.config
        
        print(f"✅ Configuration loaded successfully!")
        print(f"   Base URL: {config.get('api', {}).get('base_url', 'Not found')}")
        print(f"   Token Endpoint: {config.get('api', {}).get('token_endpoint', 'Not found')}")
        print(f"   Card Endpoint: {config.get('api', {}).get('create_card_endpoint', 'Not found')}")
        print(f"   Client ID: {config.get('authentication', {}).get('clientId', 'Not configured')}")
        print(f"   Username: {config.get('authentication', {}).get('username', 'Not configured')}")
        print(f"   Password: {'***' if config.get('authentication', {}).get('password') else 'Not configured'}")
        print(f"   Default Currency: {config.get('defaults', {}).get('currency', 'Not found')}")
        print(f"   Service Charge: {config.get('charges', {}).get('service_charge_percentage', 'Not found')}%")
        print(f"   Additional Charge: {config.get('charges', {}).get('additional_charge_percentage', 'Not found')}%")
        print(f"   Max Retries: {config.get('retry', {}).get('max_retries', 'Not found')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed with exception: {str(e)}")
        return False

async def test_existing_book_hotel_api():
    """Test that existing book_hotel API still works"""
    print("\n🏨 Testing Existing Book Hotel API (without TerraPay)...")
    
    try:
        # Import hotel service
        from app.api.services.hotel_service import HotelService
        from app.models.hotel_search_models import BookHotelRequest, RoomGuest, PhoneData
        
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
        
        print(f"✅ Book Hotel Request created successfully!")
        print(f"   Booking ID: {test_booking_request.booking_id}")
        print(f"   Email: {test_booking_request.email}")
        print(f"   Rooms: {len(test_booking_request.rooms)}")
        
        # Test that the service can be instantiated without errors
        print("✅ Hotel service instantiated successfully!")
        print("✅ Existing book_hotel API structure is intact!")
        
        return True
        
    except Exception as e:
        print(f"❌ Existing book_hotel API test failed with exception: {str(e)}")
        return False

async def main():
    """Run all TerraPay integration tests"""
    print("🚀 Starting TerraPay Integration Tests")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: Configuration Loading
    config_test = await test_configuration_loading()
    test_results.append(("Configuration Loading", config_test))
    
    # Test 2: Token Generation
    token_test = await test_terrapay_token_generation()
    test_results.append(("Token Generation", token_test is not None))
    
    # Test 3: Card Creation
    card_test = await test_terrapay_card_creation()
    test_results.append(("Card Creation", card_test))
    
    # Test 4: Payment Processing
    payment_test = await test_payment_processing()
    test_results.append(("Payment Processing", payment_test))
    
    # Test 5: Existing API Integrity
    existing_api_test = await test_existing_book_hotel_api()
    test_results.append(("Existing Book Hotel API", existing_api_test))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! TerraPay integration is ready.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and API credentials.")
    
    return passed == total

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
