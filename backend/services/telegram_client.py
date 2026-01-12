import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, Chat
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, FloodWait
from dotenv import load_dotenv

from backend.database.mongodb import get_database, Collections
from backend.services.signal_parser import signal_parser
from backend.services.webhook_sender import webhook_sender
from backend.services.notification_service import notification_service
from backend.models.schemas import (
    AvailableChannel, ParsedSignalData,
    SignalActionType, SignalStatus
)

load_dotenv()

logger = logging.getLogger(__name__)


class TelegramClientManager:
    """Manages Telegram client connection and signal extraction"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected = False
        self.is_monitoring = False
        self.user_info: Dict[str, Any] = {}
        self.monitored_channels: List[int] = []
        self.phone_code_hash: Optional[str] = None
        
        # Configuration
        self.api_id = os.getenv("TELEGRAM_API_ID", "")
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.phone = os.getenv("TELEGRAM_PHONE", "")
        self.admin_id = os.getenv("TELEGRAM_ADMIN_ID", "")
        
        # Session directory
        self.session_dir = "./sessions"
        os.makedirs(self.session_dir, exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize the Telegram client"""
        try:
            # Reload env variables
            load_dotenv(override=True)
            self.api_id = os.getenv("TELEGRAM_API_ID", "")
            self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
            self.admin_id = os.getenv("TELEGRAM_ADMIN_ID", "")
            
            if not self.api_id or not self.api_hash:
                logger.error("❌ Telegram API credentials not configured")
                return False
            
            self.client = Client(
                name="signal_extractor",
                api_id=int(self.api_id),
                api_hash=self.api_hash,
                phone_number=self.phone if self.phone else None,
                workdir=self.session_dir,
                no_updates=False
            )
            
            logger.info("✅ Telegram client initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram client: {e}")
            return False
    
    async def connect(self) -> Dict[str, Any]:
        """Connect to Telegram (may require authentication)"""
        try:
            # Reload env and initialize if needed
            if not self.client:
                initialized = await self.initialize()
                if not initialized:
                    return {
                        "success": False,
                        "error": "Failed to initialize Telegram client. Check API credentials."
                    }
            
            await self.client.start()
            
            # Get user info
            me = await self.client.get_me()
            self.user_info = {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "phone": me.phone_number
            }
            self.is_connected = True
            
            # Load monitored channels
            await self.load_monitored_channels()
            
            logger.info(f"✅ Connected as {me.username or me.first_name}")
            
            return {
                "success": True,
                "user": self.user_info
            }
            
        except SessionPasswordNeeded:
            return {
                "success": False,
                "needs_password": True,
                "message": "Two-factor authentication required"
            }
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            self.is_connected = False
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_code(self, phone_number: str) -> Dict[str, Any]:
        """Send verification code to phone number"""
        try:
            # Reload env variables
            load_dotenv()
            self.api_id = os.getenv("TELEGRAM_API_ID", "")
            self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
            
            if not self.api_id or not self.api_hash:
                return {
                    "success": False,
                    "error": "Telegram API credentials not configured. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env file"
                }
            
            # Create a new client for this phone number
            self.client = Client(
                name="signal_extractor",
                api_id=int(self.api_id),
                api_hash=self.api_hash,
                phone_number=phone_number,
                workdir=self.session_dir,
                no_updates=False
            )
            
            # Connect without starting auth flow
            await self.client.connect()
            
            # Send code
            sent_code = await self.client.send_code(phone_number)
            self.phone_code_hash = sent_code.phone_code_hash
            
            logger.info(f"✅ Verification code sent to {phone_number}")
            
            return {
                "success": True,
                "phone_code_hash": sent_code.phone_code_hash,
                "message": "Verification code sent"
            }
            
        except FloodWait as e:
            return {
                "success": False,
                "error": f"Please wait {e.value} seconds before trying again"
            }
        except Exception as e:
            logger.error(f"❌ Failed to send code: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_code(self, phone_number: str, code: str, phone_code_hash: str) -> Dict[str, Any]:
        """Verify the authentication code"""
        try:
            signed_in = await self.client.sign_in(
                phone_number=phone_number,
                phone_code_hash=phone_code_hash,
                phone_code=code
            )
            
            self.user_info = {
                "id": signed_in.id,
                "username": signed_in.username,
                "first_name": signed_in.first_name,
                "phone": signed_in.phone_number
            }
            self.is_connected = True
            
            logger.info(f"✅ Successfully signed in as {signed_in.username or signed_in.first_name}")
            
            return {
                "success": True,
                "user": self.user_info
            }
            
        except SessionPasswordNeeded:
            return {
                "success": False,
                "needs_password": True,
                "message": "Two-factor authentication required"
            }
        except PhoneCodeInvalid:
            return {
                "success": False,
                "error": "Invalid verification code"
            }
        except PhoneCodeExpired:
            return {
                "success": False,
                "error": "Verification code expired"
            }
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def verify_password(self, password: str) -> Dict[str, Any]:
        """Verify 2FA password"""
        try:
            signed_in = await self.client.check_password(password)
            
            self.user_info = {
                "id": signed_in.id,
                "username": signed_in.username,
                "first_name": signed_in.first_name,
                "phone": signed_in.phone_number
            }
            self.is_connected = True
            
            logger.info(f"✅ 2FA verified, signed in as {signed_in.username}")
            
            return {
                "success": True,
                "user": self.user_info
            }
            
        except Exception as e:
            logger.error(f"❌ Password verification failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        try:
            if self.client and self.is_connected:
                await self.client.stop()
                self.is_connected = False
                self.is_monitoring = False
                logger.info("✅ Disconnected from Telegram")
        except Exception as e:
            logger.error(f"❌ Error disconnecting: {e}")
    
    async def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        return {
            "is_connected": self.is_connected,
            "is_monitoring": self.is_monitoring,
            "user": self.user_info if self.is_connected else None,
            "monitored_channels_count": len(self.monitored_channels)
        }
    
    async def get_available_channels(self) -> List[AvailableChannel]:
        """Get all channels, groups, and supergroups the user is subscribed to"""
        if not self.is_connected or not self.client:
            logger.warning("Cannot fetch channels: not connected")
            return []
        
        channels = []
        
        try:
            # Get monitored channel IDs for comparison
            db = get_database()
            monitored = await db.channels.find({"is_active": True}).to_list(1000)
            monitored_ids = {ch["channel_id"] for ch in monitored}
            
            # Get all dialogs - iterate async generator
            dialog_count = 0
            async for dialog in self.client.get_dialogs():
                dialog_count += 1
                chat = dialog.chat
                chat_type = str(chat.type).lower().replace("chattype.", "")
                
                # Filter for channels, groups, and supergroups
                if chat_type in ["channel", "supergroup", "group"]:
                    channel = AvailableChannel(
                        channel_id=str(chat.id),
                        channel_name=chat.title or "Unknown",
                        channel_username=chat.username,
                        channel_type=chat_type,
                        members_count=getattr(chat, 'members_count', None),
                        is_already_monitored=str(chat.id) in monitored_ids
                    )
                    channels.append(channel)
            
            logger.info(f"✅ Found {len(channels)} channels/groups from {dialog_count} dialogs")
            return channels
            
        except Exception as e:
            logger.error(f"❌ Error fetching channels: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def load_monitored_channels(self):
        """Load active channels from database"""
        try:
            db = get_database()
            channels = await db.channels.find({"is_active": True}).to_list(1000)
            self.monitored_channels = [int(ch["channel_id"]) for ch in channels]
            logger.info(f"✅ Loaded {len(self.monitored_channels)} monitored channels")
        except Exception as e:
            logger.error(f"❌ Error loading channels: {e}")
    
    async def add_channel_to_monitor(self, channel_id: str, channel_name: str, channel_username: str = None, channel_type: str = None):
        """Add a channel to monitoring list"""
        try:
            db = get_database()
            
            # Upsert channel
            await db.channels.update_one(
                {"channel_id": channel_id},
                {
                    "$set": {
                        "channel_id": channel_id,
                        "channel_name": channel_name,
                        "channel_username": channel_username,
                        "channel_type": channel_type,
                        "is_active": True,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            # Update local list
            channel_id_int = int(channel_id)
            if channel_id_int not in self.monitored_channels:
                self.monitored_channels.append(channel_id_int)
            
            logger.info(f"✅ Added channel to monitor: {channel_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding channel: {e}")
            return False
    
    async def remove_channel_from_monitor(self, channel_id: str):
        """Remove a channel from monitoring"""
        try:
            db = get_database()
            await db.channels.update_one(
                {"channel_id": channel_id},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            # Update local list
            channel_id_int = int(channel_id)
            if channel_id_int in self.monitored_channels:
                self.monitored_channels.remove(channel_id_int)
            
            logger.info(f"✅ Removed channel from monitor: {channel_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error removing channel: {e}")
            return False
    
    async def start_monitoring(self):
        """Start monitoring channels for signals"""
        if not self.is_connected:
            logger.error("❌ Cannot start monitoring: not connected")
            return
        
        if self.is_monitoring:
            logger.info("⚠️ Already monitoring")
            return
        
        # Reload monitored channels
        await self.load_monitored_channels()
        
        if not self.monitored_channels:
            logger.warning("⚠️ No channels to monitor")
            return
        
        self.is_monitoring = True
        logger.info(f"🔍 Starting signal monitoring for {len(self.monitored_channels)} channels...")
        logger.info(f"📋 Monitored channel IDs: {self.monitored_channels}")
        
        try:
            # Add handler for new messages
            @self.client.on_message(filters.chat(self.monitored_channels) & (filters.text | filters.caption))
            async def handle_new_message(client, message: Message):
                logger.info(f"📨 New message received from {message.chat.title}: {message.text[:50] if message.text else 'N/A'}...")
                await self.process_message(message)
            
            # Add handler for edited messages
            @self.client.on_edited_message(filters.chat(self.monitored_channels) & (filters.text | filters.caption))
            async def handle_edited_message(client, message: Message):
                logger.info(f"✏️ Edited message received from {message.chat.title}")
                await self.process_message(message, is_edit=True)
            
            logger.info("✅ Message handlers registered successfully")
            
            # Keep monitoring
            while self.is_monitoring and self.is_connected:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"❌ Monitoring error: {e}")
            import traceback
            traceback.print_exc()
            self.is_monitoring = False
            
            # Notify admin of disconnection
            if self.admin_id:
                await notification_service.send_disconnect_notification(
                    self.admin_id,
                    f"Signal monitoring stopped due to error: {e}"
                )
    
    async def stop_monitoring(self):
        """Stop monitoring channels"""
        self.is_monitoring = False
        logger.info("⏹️ Monitoring stopped")
    
    async def process_message(self, message: Message, is_edit: bool = False):
        """Process incoming message for signal extraction"""
        try:
            text = message.text or message.caption
            if not text:
                return
            
            channel_id = str(message.chat.id)
            message_id = str(message.id)
            channel_name = message.chat.title or "Unknown"
            
            logger.info(f"🔄 Processing message from {channel_name} (ID: {channel_id})")
            logger.info(f"📝 Message text: {text[:100]}...")
            
            db = get_database()
            
            # Store raw message
            await db.raw_messages.update_one(
                {"channel_id": channel_id, "message_id": message_id},
                {
                    "$set": {
                        "channel_id": channel_id,
                        "message_id": message_id,
                        "raw_text": text,
                        "is_edit": is_edit,
                        "reply_to_message_id": str(message.reply_to_message_id) if message.reply_to_message_id else None,
                        "message_timestamp": message.date,
                        "updated_at": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "created_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            logger.info(f"💾 Raw message stored")
            
            # Check if this is a reply (potential modification)
            original_message = None
            original_signal = None
            is_reply = message.reply_to_message_id is not None
            
            if is_reply:
                # Try to get original message
                original_msg_doc = await db.raw_messages.find_one({
                    "channel_id": channel_id,
                    "message_id": str(message.reply_to_message_id)
                })
                if original_msg_doc:
                    original_message = original_msg_doc.get("raw_text")
                
                # Get original signal if exists
                original_signal = await db.signals.find_one({
                    "channel_id": channel_id,
                    "message_id": str(message.reply_to_message_id)
                })
            
            # Parse signal with AI
            logger.info(f"🤖 Parsing signal with AI...")
            parsed_data, parsing_method = await signal_parser.parse_signal(
                text,
                is_reply=is_reply,
                original_message=original_message
            )
            
            if not parsed_data:
                logger.info(f"❌ Message not identified as a signal")
                return
            
            logger.info(f"✅ Signal parsed: {parsed_data.symbol} {parsed_data.direction} @ {parsed_data.entry_price}")
            
            # If this is a modification, update original signal
            if is_reply and original_signal and parsed_data.action_type != SignalActionType.NEW:
                await self.handle_signal_modification(
                    original_signal, parsed_data, text, message, channel_name
                )
            else:
                # New signal or edited signal
                await self.handle_new_signal(
                    parsed_data, parsing_method, text, message, channel_name, is_edit
                )
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
    
    async def handle_new_signal(self, parsed_data: ParsedSignalData, parsing_method, text: str, message: Message, channel_name: str, is_edit: bool = False):
        """Handle new or edited signal"""
        db = get_database()
        channel_id = str(message.chat.id)
        message_id = str(message.id)
        
        # Build signal document
        signal_doc = {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "message_id": message_id,
            "raw_message": text,
            "symbol": parsed_data.symbol,
            "direction": parsed_data.direction.value,
            "entry_price": parsed_data.entry_price,
            "stop_loss": parsed_data.stop_loss,
            "take_profit_1": parsed_data.take_profit_1,
            "take_profit_2": parsed_data.take_profit_2,
            "take_profit_3": parsed_data.take_profit_3,
            "action_type": parsed_data.action_type.value,
            "parsing_method": parsing_method.value if parsing_method else None,
            "confidence_score": parsed_data.confidence_score,
            "notes": parsed_data.notes,
            "status": SignalStatus.PENDING.value,
            "is_edit": is_edit,
            "message_timestamp": message.date,
            "updated_at": datetime.utcnow()
        }
        
        # Upsert signal
        result = await db.signals.update_one(
            {"channel_id": channel_id, "message_id": message_id},
            {
                "$set": signal_doc,
                "$setOnInsert": {"created_at": datetime.utcnow()}
            },
            upsert=True
        )
        
        # Get the signal ID
        if result.upserted_id:
            signal_id = str(result.upserted_id)
        else:
            sig = await db.signals.find_one({"channel_id": channel_id, "message_id": message_id})
            signal_id = str(sig["_id"])
        
        logger.info(f"✅ Signal parsed: {parsed_data.symbol} {parsed_data.direction.value} @ {parsed_data.entry_price}")
        
        # Send to webhook
        await self.send_to_webhook(signal_id, signal_doc, channel_name)
    
    async def handle_signal_modification(self, original_signal: dict, parsed_data: ParsedSignalData, text: str, message: Message, channel_name: str):
        """Handle signal modification (reply with update/cancel/close)"""
        db = get_database()
        channel_id = str(message.chat.id)
        original_signal_id = str(original_signal["_id"])
        
        # Update original signal based on action type
        update_fields = {
            "updated_at": datetime.utcnow(),
            "action_type": parsed_data.action_type.value,
            "modification_message": text,
            "modification_timestamp": message.date
        }
        
        if parsed_data.action_type == SignalActionType.CANCEL:
            update_fields["status"] = SignalStatus.CANCELLED.value
        elif parsed_data.action_type == SignalActionType.CLOSE:
            update_fields["status"] = SignalStatus.CLOSED.value
        elif parsed_data.action_type in [SignalActionType.MODIFY_SL, SignalActionType.UPDATE]:
            if parsed_data.stop_loss:
                update_fields["stop_loss"] = parsed_data.stop_loss
            update_fields["status"] = SignalStatus.MODIFIED.value
        elif parsed_data.action_type == SignalActionType.MODIFY_TP:
            if parsed_data.take_profit_1:
                update_fields["take_profit_1"] = parsed_data.take_profit_1
            if parsed_data.take_profit_2:
                update_fields["take_profit_2"] = parsed_data.take_profit_2
            if parsed_data.take_profit_3:
                update_fields["take_profit_3"] = parsed_data.take_profit_3
            update_fields["status"] = SignalStatus.MODIFIED.value
        
        await db.signals.update_one(
            {"_id": original_signal["_id"]},
            {"$set": update_fields}
        )
        
        logger.info(f"✅ Signal modified: {parsed_data.action_type.value} for {original_signal.get('symbol')}")
        
        # Send modification to webhook
        updated_signal = await db.signals.find_one({"_id": original_signal["_id"]})
        await self.send_to_webhook(
            original_signal_id,
            updated_signal,
            channel_name,
            is_modification=True
        )
    
    async def send_to_webhook(self, signal_id: str, signal_doc: dict, channel_name: str, is_modification: bool = False):
        """Send signal to webhook"""
        try:
            db = get_database()
            
            # Get channel info
            channel = await db.channels.find_one({"channel_id": signal_doc["channel_id"]})
            channel_username = channel.get("channel_username") if channel else None
            
            # Build signal data dict for webhook
            signal_data = {
                "channel_id": signal_doc["channel_id"],
                "channel_name": channel_name,
                "channel_username": channel_username,
                "message_id": signal_doc["message_id"],
                "raw_message": signal_doc.get("raw_message", ""),
                "timestamp": signal_doc.get("message_timestamp", datetime.utcnow()).isoformat() if isinstance(signal_doc.get("message_timestamp"), datetime) else str(signal_doc.get("message_timestamp", datetime.utcnow().isoformat())),
                "action_type": signal_doc.get("action_type", "new"),
                "symbol": signal_doc.get("symbol"),
                "direction": signal_doc.get("direction"),
                "entry_price": signal_doc.get("entry_price"),
                "stop_loss": signal_doc.get("stop_loss"),
                "take_profit_1": signal_doc.get("take_profit_1"),
                "take_profit_2": signal_doc.get("take_profit_2"),
                "take_profit_3": signal_doc.get("take_profit_3"),
                "confidence_score": signal_doc.get("confidence_score", 1.0),
                "parsing_method": signal_doc.get("parsing_method"),
                "notes": signal_doc.get("notes"),
                "original_signal_id": signal_id if is_modification else None
            }
            
            result = await webhook_sender.send_signal(signal_data)
            
            # Update signal status
            if result["success"]:
                await db.signals.update_one(
                    {"channel_id": signal_doc["channel_id"], "message_id": signal_doc["message_id"]},
                    {
                        "$set": {
                            "status": SignalStatus.SENT.value,
                            "webhook_response": result.get("response"),
                            "sent_at": datetime.utcnow()
                        }
                    }
                )
            else:
                await db.signals.update_one(
                    {"channel_id": signal_doc["channel_id"], "message_id": signal_doc["message_id"]},
                    {
                        "$set": {
                            "status": SignalStatus.FAILED.value,
                            "error_message": result.get("error"),
                            "webhook_response": result.get("response")
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ Error sending to webhook: {e}")
            import traceback
            traceback.print_exc()


# Global instance
telegram_client = TelegramClientManager()
