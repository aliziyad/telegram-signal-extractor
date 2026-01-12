import os
import logging
import asyncio
from typing import Optional
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class NotificationService:
    """Send notifications via Telegram to admin"""
    
    def __init__(self):
        self.admin_id = os.getenv("TELEGRAM_ADMIN_ID", "")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")  # Optional: use bot for notifications
        self.client: Optional[Client] = None
    
    def set_client(self, client: Client):
        """Set the Telegram client for sending messages"""
        self.client = client
    
    async def send_disconnect_notification(self, admin_id: str, error_message: str):
        """Send notification when session disconnects"""
        try:
            if not self.client or not admin_id:
                logger.warning("⚠️ Cannot send notification: no client or admin_id")
                return False
            
            message = f"""🚨 **Signal Extractor Alert**

❌ **Session Disconnected**

**Error:** {error_message}

**Time:** {asyncio.get_event_loop().time()}

Please reconnect to resume signal monitoring."""
            
            await self.client.send_message(
                chat_id=int(admin_id),
                text=message
            )
            
            logger.info(f"✅ Disconnect notification sent to admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")
            return False
    
    async def send_status_notification(self, admin_id: str, status: str, details: str = ""):
        """Send general status notification"""
        try:
            if not self.client or not admin_id:
                return False
            
            message = f"""📊 **Signal Extractor Status**

**Status:** {status}

{details}"""
            
            await self.client.send_message(
                chat_id=int(admin_id),
                text=message
            )
            
            logger.info(f"✅ Status notification sent to admin")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send status notification: {e}")
            return False
    
    async def send_signal_notification(self, admin_id: str, signal_data: dict):
        """Send notification when a new signal is detected"""
        try:
            if not self.client or not admin_id:
                return False
            
            direction_emoji = "🟢" if signal_data.get("direction") == "BUY" else "🔴"
            
            message = f"""{direction_emoji} **New Signal Detected**

**Symbol:** {signal_data.get('symbol', 'N/A')}
**Direction:** {signal_data.get('direction', 'N/A')}
**Entry:** {signal_data.get('entry_price', 'N/A')}
**SL:** {signal_data.get('stop_loss', 'N/A')}
**TP1:** {signal_data.get('take_profit_1', 'N/A')}
**TP2:** {signal_data.get('take_profit_2', 'N/A')}
**TP3:** {signal_data.get('take_profit_3', 'N/A')}

**Channel:** {signal_data.get('channel_name', 'Unknown')}
**Method:** {signal_data.get('parsing_method', 'AI')}"""
            
            await self.client.send_message(
                chat_id=int(admin_id),
                text=message
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send signal notification: {e}")
            return False


# Global instance
notification_service = NotificationService()
