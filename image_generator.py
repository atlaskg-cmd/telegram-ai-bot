"""
AI Image Generation using Together AI (FLUX.1) with multiple fallbacks
Priority: Together AI → Hugging Face → Cloudflare → Pollinations.ai
"""

import os
import requests
import urllib.parse
import tempfile
import logging
from typing import Optional
import asyncio


class ImageGenerator:
    """
    Multi-provider image generation:
    1. Together AI (FLUX.1) - best quality, $1 free credit
    2. Hugging Face Inference - free tier
    3. Cloudflare Workers AI - if configured
    4. Pollinations.ai - always free fallback
    """
    
    def __init__(self):
        # Together AI settings (primary)
        self.together_api_key = os.environ.get("TOGETHER_API_KEY", "")
        self.together_url = "https://api.together.xyz/v1/images/generations"
        
        # Hugging Face settings (fallback 1)
        self.hf_token = os.environ.get("HF_TOKEN", "")
        self.hf_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        
        # Cloudflare settings (fallback 2)
        self.cf_api_token = os.environ.get("CF_API_TOKEN", "")
        self.cf_account_id = os.environ.get("CF_ACCOUNT_ID", "")
        self.cf_model = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
        self.cf_base_url = "https://api.cloudflare.com/client/v4/accounts"
        
        # Pollinations fallback (always available)
        self.pollinations_url = "https://image.pollinations.ai/prompt/"
        
        logging.info(f"ImageGenerator initialized:")
        logging.info(f"  - Together AI: {'✓' if self.together_api_key else '✗'}")
        logging.info(f"  - Hugging Face: {'✓' if self.hf_token else '✗'}")
        logging.info(f"  - Cloudflare: {'✓' if self.cf_api_token and self.cf_account_id else '✗'}")
        logging.info(f"  - Pollinations: ✓ (always available)")
    
    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024, 
                      seed: int = None, quality: str = "auto") -> Optional[str]:
        """
        Generate image with automatic provider selection
        
        quality: "auto", "best" (Together), "fast" (Pollinations)
        """
        # If user wants best quality or auto and Together is available - use it
        if quality in ["best", "auto"] and self.together_api_key:
            result = self._generate_together(prompt, width, height, seed)
            if result:
                return result
            logging.warning("Together AI failed, trying fallbacks...")
        
        # Try Hugging Face if available
        if self.hf_token:
            result = self._generate_huggingface(prompt, width, height, seed)
            if result:
                return result
            logging.warning("Hugging Face failed, trying next fallback...")
        
        # Try Cloudflare if configured
        if self.cf_api_token and self.cf_account_id:
            result = self._generate_cloudflare(prompt, width, height, seed)
            if result:
                return result
            logging.warning("Cloudflare failed, using final fallback...")
        
        # Final fallback - Pollinations (always works)
        return self._generate_pollinations(prompt, width, height, seed)
    
    def _generate_together(self, prompt: str, width: int = 1024, height: int = 1024, 
                          seed: int = None) -> Optional[str]:
        """Generate image using Together AI (FLUX.1 schnell) - BEST QUALITY"""
        try:
            headers = {
                "Authorization": f"Bearer {self.together_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "black-forest-labs/FLUX.1-schnell",
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": 4,  # schnell = 4 steps, fast but good quality
                "n": 1,
                "response_format": "b64_json"
            }
            
            if seed:
                data["seed"] = seed
            
            logging.info(f"[Together AI] Generating FLUX.1 image: {prompt[:50]}...")
            
            response = requests.post(
                self.together_url,
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    import base64
                    image_data = base64.b64decode(result["data"][0]["b64_json"])
                    
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.write(image_data)
                    temp_file.close()
                    
                    logging.info(f"[Together AI] Image saved to {temp_file.name}")
                    return temp_file.name
            elif response.status_code == 429:
                logging.warning("[Together AI] Rate limit reached")
            elif response.status_code == 401:
                logging.error("[Together AI] Invalid API key")
            else:
                logging.error(f"[Together AI] Error {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            logging.error(f"[Together AI] Error: {e}")
            return None
    
    def _generate_huggingface(self, prompt: str, width: int = 1024, height: int = 1024,
                             seed: int = None) -> Optional[str]:
        """Generate image using Hugging Face Inference API (FLUX.1 schnell)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.hf_token}",
                "Content-Type": "application/json"
            }
            
            # FLUX.1 schnell via Hugging Face
            payload = {
                "inputs": prompt,
                "parameters": {
                    "width": width,
                    "height": height,
                    "seed": seed if seed else -1,
                    "num_inference_steps": 4
                }
            }
            
            logging.info(f"[Hugging Face] Generating image: {prompt[:50]}...")
            
            response = requests.post(
                self.hf_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.write(response.content)
                temp_file.close()
                
                logging.info(f"[Hugging Face] Image saved to {temp_file.name}")
                return temp_file.name
            else:
                logging.error(f"[Hugging Face] Error {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            logging.error(f"[Hugging Face] Error: {e}")
            return None
    
    def _generate_cloudflare(self, prompt: str, width: int = 1024, height: int = 1024,
                            seed: int = None) -> Optional[str]:
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
            
            logging.info(f"[Cloudflare] Generating image: {prompt[:50]}...")
            
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_file.write(response.content)
                temp_file.close()
                logging.info(f"[Cloudflare] Image saved to {temp_file.name}")
                return temp_file.name
            else:
                logging.error(f"[Cloudflare] Error {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"[Cloudflare] Error: {e}")
            return None
    
    def _generate_pollinations(self, prompt: str, width: int = 1024, height: int = 1024,
                              seed: int = None) -> Optional[str]:
        """Generate image using Pollinations.ai (always free)"""
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"{self.pollinations_url}{encoded_prompt}?width={width}&height={height}&nologo=true"
            
            if seed:
                url += f"&seed={seed}"
            
            logging.info(f"[Pollinations] Generating image: {prompt[:50]}...")
            
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                temp_file.write(response.content)
                temp_file.close()
                logging.info(f"[Pollinations] Image saved to {temp_file.name}")
                return temp_file.name
            else:
                logging.error(f"[Pollinations] Error {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"[Pollinations] Error: {e}")
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
                "model": "deepseek/deepseek-r1-0528:free",
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
