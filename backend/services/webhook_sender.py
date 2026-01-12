import os
import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://zcdggtjwrtrqhqrngfau.supabase.co/functions/v1/fastsignal-webhook")
WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", "")


class WebhookSender:
    """Send parsed signals to external webhook"""
    
    def __init__(self):
        self.webhook_url = WEBHOOK_URL
        self.api_key = WEBHOOK_API_KEY
        self.timeout = 30.0
    
    def _reload_config(self):
        """Reload configuration from environment"""
        load_dotenv(override=True)
        self.api_key = os.getenv("WEBHOOK_API_KEY", "")
        self.webhook_url = os.getenv("WEBHOOK_URL", "https://zcdggtjwrtrqhqrngfau.supabase.co/functions/v1/fastsignal-webhook")
    
    async def send_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a signal to the webhook endpoint
        
        Args:
            signal_data: Dictionary with signal information
            
        Returns:
            Dict with success status and response data
        """
        self._reload_config()
        
        try:
            headers = {
                "Content-Type": "application/json",
            }
            
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                headers["x-api-key"] = self.api_key
            
            # Build payload with exact field names the external system expects
            payload = {
                "channel_telegram_id": signal_data.get("channel_id"),
                "channel_name": signal_data.get("channel_name"),
                "channel_username": signal_data.get("channel_username"),
                "message_id": signal_data.get("message_id"),
                "raw_message": signal_data.get("raw_message"),
                "timestamp": signal_data.get("timestamp", datetime.utcnow().isoformat()),
                "action_type": signal_data.get("action_type", "new"),
                "parsed_signal": {
                    "symbol": signal_data.get("symbol"),
                    "direction": signal_data.get("direction"),
                    "entry_price": signal_data.get("entry_price"),
                    "stop_loss": signal_data.get("stop_loss"),
                    "take_profit_1": signal_data.get("take_profit_1"),
                    "take_profit_2": signal_data.get("take_profit_2"),
                    "take_profit_3": signal_data.get("take_profit_3"),
                    "confidence_score": signal_data.get("confidence_score", 1.0),
                    "parsing_method": signal_data.get("parsing_method"),
                    "notes": signal_data.get("notes")
                }
            }
            
            # Add original_signal_id for modifications
            if signal_data.get("original_signal_id"):
                payload["original_signal_id"] = signal_data["original_signal_id"]
            
            logger.info(f"📤 Sending signal to webhook: {self.webhook_url}")
            logger.info(f"📦 Payload: {payload}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers=headers
                )
                
                response_data = {
                    "status_code": response.status_code,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                
                try:
                    response_data["body"] = response.json()
                except:
                    response_data["body"] = response.text
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"✅ Signal sent successfully to webhook: {response.status_code}")
                    return {
                        "success": True,
                        "response": response_data
                    }
                else:
                    logger.error(f"❌ Webhook returned error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "response": response_data
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"❌ Webhook timeout after {self.timeout}s")
            return {
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"❌ Webhook error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }


# Global sender instance
webhook_sender = WebhookSender()
