#!/usr/bin/env python3
"""
Admin Dashboard Verification Script
Tests authentication, configuration management, and live call monitoring endpoints
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "BankABC@2026"

def test_login():
    """Test admin login endpoint"""
    print("🔐 Testing admin login...")
    response = requests.post(
        f"{BASE_URL}/admin/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Login successful! Token: {data['access_token'][:20]}...")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        sys.exit(1)

def test_login_failure():
    """Test login with incorrect credentials"""
    print("\n🔐 Testing login with wrong credentials...")
    response = requests.post(
        f"{BASE_URL}/admin/login",
        json={"username": "wrong", "password": "wrong"}
    )
    
    if response.status_code == 401:
        print("✅ Correctly rejected invalid credentials")
    else:
        print(f"❌ Unexpected response: {response.status_code}")

def test_verify_token(token):
    """Test token verification endpoint"""
    print("\n🔍 Testing token verification...")
    response = requests.post(
        f"{BASE_URL}/admin/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Token verified: {data['message']}")
    else:
        print(f"❌ Token verification failed: {response.status_code}")

def test_get_config(token):
    """Test getting configuration"""
    print("\n📋 Testing GET configuration...")
    response = requests.get(
        f"{BASE_URL}/admin/config",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Configuration retrieved successfully")
        print(f"   - System persona: {data.get('system_persona', '')[:50]}...")
        print(f"   - Greeting: {data.get('greeting', '')}")
        return data
    else:
        print(f"❌ Failed to get configuration: {response.status_code}")
        return None

def test_update_config(token, original_config):
    """Test updating configuration"""
    print("\n📝 Testing PUT configuration...")
    
    # Make a small change to the greeting
    modified_config = original_config.copy()
    original_greeting = modified_config.get('greeting', '')
    test_greeting = "TEST: Welcome to Bank ABC Admin Dashboard Test"
    modified_config['greeting'] = test_greeting
    
    response = requests.put(
        f"{BASE_URL}/admin/config",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"config": modified_config}
    )
    
    if response.status_code == 200:
        print(f"✅ Configuration updated successfully")
        
        # Verify the change
        verify_response = requests.get(
            f"{BASE_URL}/admin/config",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if verify_response.status_code == 200:
            updated_data = verify_response.json()
            if updated_data.get('greeting') == test_greeting:
                print(f"✅ Change verified in configuration")
                
                # Restore original
                modified_config['greeting'] = original_greeting
                restore_response = requests.put(
                    f"{BASE_URL}/admin/config",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    json={"config": modified_config}
                )
                
                if restore_response.status_code == 200:
                    print(f"✅ Original configuration restored")
                else:
                    print(f"⚠️  Warning: Failed to restore original config")
            else:
                print(f"❌ Change not reflected in configuration")
    else:
        print(f"❌ Failed to update configuration: {response.status_code} - {response.text}")

def test_live_calls(token):
    """Test live calls monitoring endpoint"""
    print("\n📞 Testing live calls monitoring...")
    response = requests.get(
        f"{BASE_URL}/admin/calls/live",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Live calls endpoint working")
        print(f"   - Active calls: {len(data)}")
        if data:
            for call in data:
                print(f"   - Call ID: {call['call_id'][:8]}... | Customer: {call.get('customer_id', 'N/A')} | Verified: {call['is_verified']}")
    else:
        print(f"❌ Failed to get live calls: {response.status_code}")

def main():
    print("=" * 60)
    print("Admin Dashboard Verification")
    print("=" * 60)
    
    # Test login
    token = test_login()
    
    # Test login failure
    test_login_failure()
    
    # Test token verification
    test_verify_token(token)
    
    # Test configuration endpoints
    config = test_get_config(token)
    if config:
        test_update_config(token, config)
    
    # Test live calls monitoring
    test_live_calls(token)
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to backend server.")
        print("   Make sure the backend is running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
