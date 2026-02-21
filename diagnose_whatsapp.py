#!/usr/bin/env python3
"""
Diagnostic script for WhatsApp bot.
Checks configuration and connectivity to Green API.
"""
import os
import sys
import requests
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import validate_config, whatsapp_config


def check_environment():
    """Check environment variables."""
    print("[CHECK] Checking Environment Variables...")
    
    green_api_id = os.environ.get("GREEN_API_ID")
    green_api_token = os.environ.get("GREEN_API_TOKEN")
    
    print(f"GREEN_API_ID: {'SET' if green_api_id else 'NOT SET'}")
    print(f"GREEN_API_TOKEN: {'SET' if green_api_token else 'NOT SET'}")
    
    if not green_api_id or not green_api_token:
        print("\n[ERROR] WhatsApp bot will not work without Green API credentials!")
        print("\nTo fix this, set environment variables:")
        print("  export GREEN_API_ID='your_instance_id'")
        print("  export GREEN_API_TOKEN='your_api_token'")
        print("\nOr see GREEN_API_SETUP.md for instructions")
        return False
    
    return True


def check_api_connectivity(api_id, api_token):
    """Test connectivity to Green API."""
    print("\n[CHECK] Testing Green API Connectivity...")
    
    api_url = "https://api.green-api.com"
    
    # Test endpoint to check if instance is working
    test_url = f"{api_url}/waInstance{api_id}/GetSettings/{api_token}"
    
    try:
        response = requests.get(test_url, timeout=10)
        print(f"API Request: GET {test_url}")
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[SUCCESS] Successfully connected to Green API")
            try:
                data = response.json()
                print(f"Instance Status: {data.get('accountStatus', 'Unknown')}")
                print(f"Phone Number: {data.get('phoneNumber', 'Not set')}")
                return True
            except:
                print("[WARNING] Could not parse response, but connection successful")
                return True
        elif response.status_code == 400:
            print("[ERROR] Invalid credentials or instance ID")
            print("   Check if your GREEN_API_ID and GREEN_API_TOKEN are correct")
            return False
        elif response.status_code == 402:
            print("[ERROR] Payment required - account not activated")
            print("   Check your Green API subscription status")
            return False
        else:
            print(f"[ERROR] API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] Request timed out - check your internet connection")
        return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection error - check your internet connection")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False


def check_whatsapp_adapter():
    """Check if WhatsApp adapter can be imported and initialized."""
    print("\n[CHECK] Testing WhatsApp Adapter...")
    
    try:
        from adapters.whatsapp_full import FullWhatsAppBot
        print("[SUCCESS] WhatsApp adapter imported successfully")
        
        # Try to initialize the bot
        bot = FullWhatsAppBot()
        
        if bot.enabled:
            print("[SUCCESS] WhatsApp bot initialized successfully")
            print(f"   Instance ID: {bot.id_instance[:8]}..." if bot.id_instance else "   No instance ID")
            return True
        else:
            print("[ERROR] WhatsApp bot is disabled (likely missing credentials)")
            return False
            
    except ImportError as e:
        print(f"[ERROR] Could not import WhatsApp adapter: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error initializing WhatsApp bot: {e}")
        return False


def check_green_api_setup():
    """Provide guidance on Green API setup."""
    print("\n[INFO] Green API Setup Information:")
    print("1. Register at: https://console.green-api.com/")
    print("2. Create an instance (choose Developer plan for testing)")
    print("3. Get your IdInstance and ApiTokenInstance")
    print("4. Scan QR code with WhatsApp on your phone")
    print("5. Set environment variables as mentioned above")


def main():
    """Main diagnostic function."""
    print("[DIAGNOSTIC] WhatsApp Bot Diagnostic Tool")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Check environment
    env_ok = check_environment()
    all_checks_passed &= env_ok
    
    if env_ok:
        # Check API connectivity
        api_ok = check_api_connectivity(
            os.environ.get("GREEN_API_ID"),
            os.environ.get("GREEN_API_TOKEN")
        )
        all_checks_passed &= api_ok
        
        # Check adapter
        adapter_ok = check_whatsapp_adapter()
        all_checks_passed &= adapter_ok
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("[SUCCESS] All checks passed! WhatsApp bot should work correctly.")
        print("\nNote: WhatsApp bot runs in a separate thread in the main application.")
        print("Make sure to start the main app with: python main.py")
    else:
        print("[ERROR] Some checks failed. Please address the issues above.")
        print("\nFor help setting up Green API, see GREEN_API_SETUP.md")
        check_green_api_setup()
        
    return all_checks_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)