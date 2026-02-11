"""
Crypto Price Tracker using CoinGecko API (free tier)
"""

import requests
import logging
from typing import Dict, List, Optional

# Popular coins mapping (symbol -> coin_id for CoinGecko)
POPULAR_COINS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'USDT': 'tether',
    'BNB': 'binancecoin',
    'SOL': 'solana',
    'USDC': 'usd-coin',
    'XRP': 'ripple',
    'DOGE': 'dogecoin',
    'TON': 'toncoin',
    'ADA': 'cardano',
    'AVAX': 'avalanche-2',
    'DOT': 'polkadot',
    'MATIC': 'matic-network',
    'LINK': 'chainlink',
    'LTC': 'litecoin',
    'BCH': 'bitcoin-cash',
    'UNI': 'uniswap',
    'ATOM': 'cosmos',
    'XLM': 'stellar',
    'ALGO': 'algorand',
    'PEPE': 'pepe',
    'SHIB': 'shiba-inu',
}

class CryptoTracker:
    """Track cryptocurrency prices using CoinGecko API"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.vs_currency = "usd"
        
    def get_price(self, coin_id: str) -> Optional[Dict]:
        """Get current price for a coin"""
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': self.vs_currency,
                'include_24hr_change': 'true',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    return {
                        'price': data[coin_id]['usd'],
                        'change_24h': data[coin_id].get('usd_24h_change', 0),
                        'market_cap': data[coin_id].get('usd_market_cap', 0),
                        'volume_24h': data[coin_id].get('usd_24h_vol', 0)
                    }
            elif response.status_code == 429:
                logging.warning("CoinGecko rate limit reached")
                return {'error': 'rate_limit'}
            else:
                logging.error(f"CoinGecko error: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error fetching crypto price: {e}")
            return None
    
    def get_multiple_prices(self, coin_ids: List[str]) -> Dict[str, Dict]:
        """Get prices for multiple coins"""
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': self.vs_currency,
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                result = {}
                for coin_id in coin_ids:
                    if coin_id in data:
                        result[coin_id] = {
                            'price': data[coin_id]['usd'],
                            'change_24h': data[coin_id].get('usd_24h_change', 0),
                            'market_cap': data[coin_id].get('usd_market_cap', 0)
                        }
                return result
            else:
                logging.error(f"CoinGecko error: {response.status_code}")
                return {}
        except Exception as e:
            logging.error(f"Error fetching multiple prices: {e}")
            return {}
    
    def search_coin(self, query: str) -> Optional[Dict]:
        """Search for a coin by name or symbol"""
        query_upper = query.upper()
        
        # Check popular coins first
        if query_upper in POPULAR_COINS:
            return {
                'id': POPULAR_COINS[query_upper],
                'symbol': query_upper,
                'name': query_upper
            }
        
        # Try to search via API
        try:
            url = f"{self.base_url}/search"
            params = {'query': query}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                coins = data.get('coins', [])
                if coins:
                    return {
                        'id': coins[0]['id'],
                        'symbol': coins[0]['symbol'].upper(),
                        'name': coins[0]['name']
                    }
            return None
        except Exception as e:
            logging.error(f"Error searching coin: {e}")
            return None
    
    def get_trending(self) -> List[Dict]:
        """Get trending coins"""
        try:
            url = f"{self.base_url}/search/trending"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                coins = data.get('coins', [])
                result = []
                for item in coins[:7]:  # Top 7
                    coin = item['item']
                    result.append({
                        'id': coin['id'],
                        'symbol': coin['symbol'].upper(),
                        'name': coin['name'],
                        'market_cap_rank': coin.get('market_cap_rank', 'N/A')
                    })
                return result
            return []
        except Exception as e:
            logging.error(f"Error fetching trending: {e}")
            return []
    
    def get_top_coins(self, limit: int = 10) -> List[Dict]:
        """Get top coins by market cap"""
        try:
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': self.vs_currency,
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false'
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return [{
                    'id': coin['id'],
                    'symbol': coin['symbol'].upper(),
                    'name': coin['name'],
                    'price': coin['current_price'],
                    'change_24h': coin['price_change_percentage_24h'],
                    'market_cap': coin['market_cap'],
                    'rank': coin['market_cap_rank']
                } for coin in data]
            return []
        except Exception as e:
            logging.error(f"Error fetching top coins: {e}")
            return []
    
    def format_price(self, price: float) -> str:
        """Format price with appropriate decimals"""
        if price >= 1:
            return f"${price:,.2f}"
        elif price >= 0.01:
            return f"${price:.4f}"
        else:
            return f"${price:.8f}"
    
    def format_change(self, change: float) -> str:
        """Format price change with emoji"""
        if change > 0:
            return f"🟢 +{change:.2f}%"
        elif change < 0:
            return f"🔴 {change:.2f}%"
        else:
            return "⚪ 0.00%"


# Global instance
crypto = CryptoTracker()
