import aiohttp
import json

class Shortener:
    def __init__(self, config):
        self.config = config
    
    async def shorten_url(self, url: str) -> str:
        """Shorten URL using ModijiUrl"""
        shortener_config = self.config.get('shortener', {})
        if not shortener_config.get('enabled'):
            return url
            
        api_key = shortener_config.get('api_key')
        api_url = shortener_config.get('api_url')
        
        if not api_key or not api_url:
            return url
            
        try:
            params = {
                'api': api_key,
                'url': url,
                'format': 'text'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        short_url = await response.text()
                        return short_url.strip()
            
        except Exception as e:
            print(f"Error shortening URL: {str(e)}")
            
        return url 