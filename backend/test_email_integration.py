#!/usr/bin/env python3
"""
Test script to verify email integration in auth routes
"""
import asyncio
import os
import sys
import requests
import json

# Add backend root to path
backend_root = os.path.dirname(__file__)
sys.path.insert(0, backend_root)

async def test_complete_flow():
    """Test the complete registration and verification flow"""
    base_url = "http://localhost:8000/api/v1/auth"
    test_email = "taperfadehub@gmail.com"
    test_password = "TestPass123!"
    
    print("🧪 Testing Complete Email Verification Flow")
    print("=" * 50)
    
    # Step 1: Register
    print("📝 Step 1: Registration")
    register_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(f"{base_url}/register", json=register_data)
        print(f"Registration response status: {response.status_code}")
        print(f"Registration response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Registration endpoint working")
        else:
            print("❌ Registration failed")
            return
            
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return
    
    # Step 2: Send verification code directly 
    print("\n📧 Step 2: Sending verification code directly")
    try:
        from services.email_service import EmailService
        import random
        import string
        
        # Generate verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        print(f"Generated verification code: {verification_code}")
        
        # Send email
        email_service = EmailService()
        result = await email_service.send_verification_code(test_email, verification_code)
        print(f"Direct email send result: {result}")
        
        if result:
            print("✅ Email service working")
            print(f"📬 Check your email for code: {verification_code}")
            
            # Step 3: Test verification (this will fail because code isn't in system)
            print(f"\n🔐 Step 3: Testing verification with code {verification_code}")
            verify_data = {
                "email": test_email,
                "verification_code": verification_code
            }
            
            verify_response = requests.post(f"{base_url}/verify-email", json=verify_data)
            print(f"Verification response status: {verify_response.status_code}")
            print(f"Verification response: {verify_response.json()}")
            
            return verification_code
        else:
            print("❌ Email service failed")
            
    except Exception as e:
        print(f"❌ Email service error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    code = asyncio.run(test_complete_flow())
    if code:
        print(f"\n📋 Summary:")
        print(f"✅ Registration endpoint: Working")
        print(f"✅ Email service: Working")
        print(f"❌ Integration: Email not sent during registration")
        print(f"🔐 Test code sent directly: {code}")
        print(f"\n💡 Next: Check email and test verification manually")
