"""
Simple WhatsApp test - checks if Green API is receiving messages
"""
import os
import time
import requests

# Get credentials from environment
api_id = os.environ.get("GREEN_API_ID")
api_token = os.environ.get("GREEN_API_TOKEN")

if not api_id or not api_token:
    print("❌ Set GREEN_API_ID and GREEN_API_TOKEN environment variables")
    exit(1)

print(f"Testing Green API connection...")
print(f"Instance ID: {api_id[:5]}...")

# Check settings
url = f"https://api.green-api.com/waInstance{api_id}/GetSettings/{api_token}"
resp = requests.get(url, timeout=30)
print(f"GetSettings status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    print(f"Bot phone: {data.get('wid', 'unknown')}")
    print(f"Webhook URL: {data.get('webhookUrl', 'not set')}")

print("\n" + "="*60)
print("Waiting for incoming messages...")
print("Send 'привет' to the bot number in WhatsApp now!")
print("="*60 + "\n")

# Poll for messages
for i in range(30):  # 30 attempts = ~2.5 minutes
    try:
        url = f"https://api.green-api.com/waInstance{api_id}/ReceiveNotification/{api_token}"
        resp = requests.get(url, timeout=35)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if data and data.get("receiptId"):
                receipt_id = data["receiptId"]
                body = data.get("body", {})
                webhook_type = body.get("typeWebhook", "unknown")
                
                print(f"✅ Received: {webhook_type}")
                
                if webhook_type == "incomingMessageReceived":
                    sender = body.get("senderData", {}).get("sender", "unknown")
                    msg_data = body.get("messageData", {})
                    msg_type = msg_data.get("typeMessage", "unknown")
                    
                    if msg_type == "textMessage":
                        text = msg_data.get("textMessageData", {}).get("textMessage", "")
                        print(f"📱 From: {sender}")
                        print(f"💬 Text: {text}")
                        
                        # Reply back
                        reply_url = f"https://api.green-api.com/waInstance{api_id}/SendMessage/{api_token}"
                        payload = {
                            "chatId": sender,
                            "message": f"✅ Бот работает! Получил: '{text}'"
                        }
                        send_resp = requests.post(reply_url, json=payload, timeout=30)
                        print(f"📤 Reply sent: {send_resp.status_code}")
                
                # Delete notification
                del_url = f"https://api.green-api.com/waInstance{api_id}/DeleteNotification/{api_token}/{receipt_id}"
                requests.delete(del_url, timeout=10)
            else:
                print(f"[{i+1}/30] No new messages...")
        else:
            print(f"[{i+1}/30] Error: HTTP {resp.status_code}")
            
    except Exception as e:
        print(f"[{i+1}/30] Error: {e}")
    
    time.sleep(5)

print("\nTest completed!")
