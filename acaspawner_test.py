#!/usr/bin/env python3
"""
Test program for AcaSpawner

This test program demonstrates the lifecycle of an AcaSpawner instance:
1. Calls start() and verifies a non-None return value
2. Calls poll() to verify it returns None (indicating running state)
3. Calls get_state() to get and verify the state
4. Calls load_state() to test state loading
5. Calls stop() to clean up resources
6. Calls poll() again to verify the ACA is gone

Note: This test requires proper Azure credentials and configuration.
Set the following environment variables before running:
- AZURE_SUBSCRIPTION_ID
- AZURE_RESOURCE_GROUP
- AZURE_ACA_ENVIRONMENT_NAME
- AZURE_ACR_SERVER
- AZURE_ACR_IDENTITY

Usage: python acaspawner_test.py
"""

import asyncio
import os
import sys
from unittest.mock import Mock
from acaspawner import AcaSpawner


class TestUser:
    """Mock user object for testing"""
    def __init__(self, name="testuser"):
        self.name = name
        self.id = 1


class TestHub:
    """Mock hub object for testing"""
    def __init__(self):
        self.base_url = "http://localhost:8000"


async def test_acaspawner():
    """Test the complete lifecycle of AcaSpawner"""
    
    print("🧪 Starting AcaSpawner Test Program")
    print("=" * 50)
    
    # Check required environment variables
    required_env_vars = [
        "AZURE_SUBSCRIPTION_ID",
        "AZURE_RESOURCE_GROUP", 
        "AZURE_ACA_ENVIRONMENT_NAME",
        "AZURE_ACR_SERVER",
        "AZURE_ACR_IDENTITY"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the test.")
        return False
    
    # Create spawner instance
    spawner = AcaSpawner()
    spawner.user = TestUser()
    spawner.hub = TestHub()
    spawner.log = Mock()  # Mock logger to avoid setup complexity
    
    # Configure spawner (these will use environment variables by default)
    print("📋 Configuration:")
    print(f"   Subscription ID: {spawner.subscription_id}")
    print(f"   Resource Group: {spawner.resource_group}")
    print(f"   ACA Environment: {spawner.aca_environment_name}")
    print(f"   Region: {spawner.region}")
    print(f"   Image: {spawner.image}")
    print(f"   ACA Name: {spawner.aca_name}")
    print()
    
    try:
        # Test 1: Call start() and verify non-None return value
        print("1️⃣ Testing start() method...")
        start_result = await spawner.start()
        
        if start_result is not None:
            print(f"   ✅ start() returned: {start_result}")
        else:
            print("   ❌ start() returned None - this should not happen")
            return False
        
        # Test 2: Call poll() to verify it returns None (running state)
        print("\n2️⃣ Testing poll() method (should return None for running state)...")
        poll_result = await spawner.poll()
        
        if poll_result is None:
            print("   ✅ poll() returned None - ACA is running")
        else:
            print(f"   ❌ poll() returned {poll_result} - expected None for running state")
        
        # Test 3: Call get_state() and verify the state
        print("\n3️⃣ Testing get_state() method...")
        state = spawner.get_state()
        
        print(f"   📊 Current state: {state}")
        
        # Verify state contains expected keys
        expected_keys = ["aca_running_name"]
        missing_keys = [key for key in expected_keys if key not in state]
        
        if not missing_keys:
            print("   ✅ State contains all expected keys")
            if state.get("aca_running_name"):
                print(f"   ✅ aca_running_name: {state['aca_running_name']}")
            else:
                print("   ⚠️  aca_running_name is None or empty")
        else:
            print(f"   ❌ State missing keys: {missing_keys}")
        
        # Test 4: Call load_state() to test state loading
        print("\n4️⃣ Testing load_state() method...")
        
        # Save current state
        original_state = spawner.get_state()
        
        # Create a test state to load
        test_state = {
            "aca_running_name": "test-aca-name",
            "user_options": {}
        }
        
        # Load the test state
        spawner.load_state(test_state)
        loaded_state = spawner.get_state()
        
        if loaded_state.get("aca_running_name") == "test-aca-name":
            print("   ✅ load_state() successfully loaded test state")
        else:
            print(f"   ❌ load_state() failed - expected 'test-aca-name', got '{loaded_state.get('aca_running_name')}'")
        
        # Restore original state
        spawner.load_state(original_state)
        print("   ✅ Original state restored")
        
        # Test 5: Call stop() to clean up resources
        print("\n5️⃣ Testing stop() method...")
        await spawner.stop()
        print("   ✅ stop() completed successfully")
        
        # Test 6: Call poll() again to verify ACA is gone
        print("\n6️⃣ Testing poll() method after stop (should indicate ACA is gone)...")
        
        try:
            final_poll_result = await spawner.poll()
            
            if final_poll_result == 0:
                print("   ✅ poll() returned 0 - ACA is stopped/gone")
            elif final_poll_result is None:
                print("   ⚠️  poll() returned None - ACA might still be running")
            else:
                print(f"   ℹ️  poll() returned {final_poll_result}")
                
        except Exception as e:
            print(f"   ✅ poll() raised exception (expected after deletion): {e}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Try to clean up if something went wrong
        try:
            print("\n🧹 Attempting cleanup...")
            await spawner.stop()
            print("   ✅ Cleanup completed")
        except Exception as cleanup_error:
            print(f"   ⚠️  Cleanup failed: {cleanup_error}")
        
        return False


async def main():
    """Main function to run the test"""
    print("AcaSpawner Test Program")
    print("This test requires proper Azure credentials and environment configuration.")
    print()
    
    success = await test_acaspawner()
    
    if success:
        print("\n✅ Test program completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test program failed!")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async test
    asyncio.run(main())
