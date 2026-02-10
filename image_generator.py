"""
AI Image Generation using Free Models via OpenRouter
- ByteDance Seedream 4.5 (free) for images
- DeepSeek R1 (free) for advanced chat
"""

import os
import requests
import base64
import tempfile
import logging
from typing import Optional


class ImageGenerator:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/images/generations"
    
    def generate_image(self, prompt: str, size: str = "1024x1024", quality: str = "standard") -> Optional[str]:
        """
        Generate image using DALL-E via OpenRouter
        Returns path to saved image file
        """
        if not self.api_key:
            logging.error("OPENROUTER_API_KEY not set")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "bytedance/seedream-4.5:free",
                "prompt": prompt,
                "n": 1,
                "size": size,
                "quality": quality  # "standard" or "hd"
            }
            
            logging.info(f"Generating image for prompt: {prompt[:50]}...")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # DALL-E returns URL or base64
                if "data" in result and len(result["data"]) > 0:
                    image_data = result["data"][0]
                    
                    # If URL provided
                    if "url" in image_data:
                        return self._download_image(image_data["url"])
                    
                    # If base64 provided
                    elif "b64_json" in image_data:
                        return self._save_base64_image(image_data["b64_json"])
                
                logging.error(f"Unexpected response format: {result}")
                return None
            else:
                logging.error(f"Image generation failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error generating image: {e}")
            return None
    
    def _download_image(self, url: str) -> Optional[str]:
        """Download image from URL and save to temp file"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Determine extension from content-type
                content_type = response.headers.get('content-type', '')
                if 'png' in content_type:
                    ext = '.png'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                else:
                    ext = '.png'
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                temp_file.write(response.content)
                temp_file.close()
                return temp_file.name
            else:
                logging.error(f"Failed to download image: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error downloading image: {e}")
            return None
    
    def _save_base64_image(self, b64_data: str) -> Optional[str]:
        """Save base64 encoded image to temp file"""
        try:
            image_bytes = base64.b64decode(b64_data)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_file.write(image_bytes)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            logging.error(f"Error saving base64 image: {e}")
            return None


class DeepSeekChat:
    """DeepSeek R1 (free) via OpenRouter for advanced chat"""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def chat(self, messages: list, max_tokens: int = 2000) -> str:
        """
        Chat with GPT-4 Turbo
        messages: list of dicts with 'role' and 'content'
        """
        if not self.api_key:
            return "❌ OPENROUTER_API_KEY не установлен"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek/deepseek-r1-0528:free",  # DeepSeek R1 Free
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            logging.info(f"Sending request to DeepSeek R1 (free)")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return "❌ Пустой ответ от API"
            elif response.status_code == 429:
                return "❌ Превышен лимит запросов. Попробуйте позже."
            elif response.status_code == 401:
                return "❌ Ошибка авторизации. Проверьте API ключ."
            else:
                logging.error(f"GPT-4 error: {response.status_code} - {response.text}")
                return f"❌ Ошибка API: {response.status_code}"
                
        except Exception as e:
            logging.error(f"Error in DeepSeek chat: {e}")
            return f"❌ Ошибка: {e}"
    
    def simple_chat(self, user_message: str) -> str:
        """Simple single message chat"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Answer in the same language as the user's question."},
            {"role": "user", "content": user_message}
        ]
        return self.chat(messages)
