"""
AI Image Generation using Cloudflare Workers AI (free tier: 10k requests/day)
Fallback to Pollinations.ai if Cloudflare not configured
DeepSeek R1 via OpenRouter (free) for advanced chat
"""

import os
import requests
import urllib.parse
import tempfile
import logging
from typing import Optional
import asyncio


class ImageGenerator:
    """Image generation using Cloudflare Workers AI with fallback to Pollinations.ai"""
    
    def __init__(self):
        # Cloudflare Workers AI settings
        self.cf_api_token = os.environ.get("CF_API_TOKEN", "")
        self.cf_account_id = os.environ.get("CF_ACCOUNT_ID", "")
        self.cf_model = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
        self.cf_base_url = "https://api.cloudflare.com/client/v4/accounts"
        
        # Fallback to Pollinations.ai
        self.pollinations_url = "https://image.pollinations.ai/prompt/"
        
        # Check which service is available
        self.use_cloudflare = bool(self.cf_api_token and self.cf_account_id)
        
        if self.use_cloudflare:
            logging.info("ImageGenerator: Using Cloudflare Workers AI")
        else:
            logging.info("ImageGenerator: Using Pollinations.ai (fallback)")
    
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024, seed: int = None) -> Optional[str]:
        """
        Generate image using Cloudflare Workers AI or fallback to Pollinations.ai
        Returns path to saved image file
        """
        # Try Cloudflare first if configured
        if self.use_cloudflare:
            result = self._generate_cloudflare(prompt, width, height, seed)
            if result:
                return result
            logging.warning("Cloudflare failed, trying Pollinations.ai fallback...")
        
        # Fallback to Pollinations.ai
        return self._generate_pollinations(prompt, width, height, seed)
    
    def _generate_cloudflare(self, prompt: str, width: int = 1024, height: int = 1024, seed: int = None) -> Optional[str]:
        """Generate image using Cloudflare Workers AI"""
        try:
            url = f"{self.cf_base_url}/{self.cf_account_id}/ai/run/{self.cf_model}"
            
            headers = {
                "Authorization": f"Bearer {self.cf_api_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "prompt": prompt,
                "width": width,
                "height": height
            }
            
            if seed:
                data["seed"] = seed
            
            logging.info(f"Generating image with Cloudflare AI: {prompt[:50]}...")
            
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            if response.status_code == 200:
                # Save binary image data to temp file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.write(response.content)
                temp_file.close()
                logging.info(f"Image saved to {temp_file.name}")
                return temp_file.name
            else:
                logging.error(f"Cloudflare AI error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"Error generating image with Cloudflare: {e}")
            return None
    
    def _generate_pollinations(self, prompt: str, width: int = 1024, height: int = 1024, seed: int = None) -> Optional[str]:
        """Generate image using Pollinations.ai (fallback)"""
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"{self.pollinations_url}{encoded_prompt}?width={width}&height={height}&nologo=true"
            
            if seed:
                url += f"&seed={seed}"
            
            logging.info(f"Generating image with Pollinations.ai: {prompt[:50]}...")
            
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_file.write(response.content)
                temp_file.close()
                logging.info(f"Image saved to {temp_file.name}")
                return temp_file.name
            else:
                logging.error(f"Pollinations.ai error: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Error generating image with Pollinations: {e}")
            return None


class DeepSeekChat:
    """DeepSeek R1 (free) via OpenRouter for advanced chat"""
    
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def chat(self, messages: list, max_tokens: int = 2000) -> str:
        """
        Chat with DeepSeek R1 (free)
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
                logging.error(f"DeepSeek error: {response.status_code} - {response.text}")
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
