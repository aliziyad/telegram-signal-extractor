import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from pyrogram import Client, filters
from pyrogram.types import Message
from sqlalchemy.orm import Session
from app.database.models import TelegramChannel, RawSignal, ParsedSignal, ExtractionLog
from app.database.connection import SessionLocal
from app.extractors.signal_parser import SignalParser
from config.settings import settings

logger = logging.getLogger(__name__)

class TelegramSignalExtractor:
    def __init__(self):
        self.client = None
        self.parser = SignalParser()
        self.is_running = False
        self.channels_to_monitor = []
        
    async def initialize(self):
        """Initialize Telegram client with Pyrogram"""
        try:
            self.client = Client(
                name="signal_extractor",
                api_id=settings.TELEGRAM_API_ID,
                api_hash=settings.TELEGRAM_API_HASH,
                phone_number=settings.TELEGRAM_PHONE,
                workdir="./sessions",
                no_updates=False
            )
            
            await self.client.start()
            me = await self.client.get_me()
            logger.info(f"✓ Telegram client connected as {me.username or me.first_name}")
            
            # Load channels from database
            await self.load_channels_from_db()
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            raise
    
    async def load_channels_from_db(self):
        """Load active channels from database"""
        db = SessionLocal()
        try:
            channels = db.query(TelegramChannel).filter(
                TelegramChannel.is_active == True
            ).all()
            
            self.channels_to_monitor = [int(ch.channel_id) for ch in channels]
            logger.info(f"Loaded {len(self.channels_to_monitor)} channels from database")
            
        except Exception as e:
            logger.error(f"Failed to load channels: {e}")
        finally:
            db.close()
    
    async def start_monitoring(self):
        """Start monitoring channels for signals"""
        if not self.client:
            await self.initialize()
        
        self.is_running = True
        logger.info("🔍 Starting signal monitoring...")
        
        try:
            # Set up handlers for new messages
            @self.client.on_message(filters.chat(self.channels_to_monitor) & filters.text)
            async def on_new_message(client, message: Message):
                await self.process_message(message)
            
            logger.info("Message handlers registered")
            
            # Keep the client running
            await self.client.idle()
            
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
            self.is_running = False
            raise
    
    async def process_message(self, message: Message):
        """Process incoming message for signal extraction"""
        try:
            if not message.text:
                return
            
            db = SessionLocal()
            
            try:
                # Get channel info
                channel = message.chat
                channel_id = str(channel.id)
                
                # Store raw message
                raw_signal = RawSignal(
                    channel_id=channel_id,
                    message_id=str(message.id),
                    raw_message=message.text,
                    message_timestamp=message.date
                )
                db.add(raw_signal)
                db.commit()
                
                logger.info(f"Raw signal stored: {channel.title} | {message.id}")
                
                # Parse signal
                parsed_data, parsing_method = self.parser.parse_signal(
                    message.text,
                    channel.title or "unknown"
                )
                
                if parsed_data:
                    # Store parsed signal
                    parsed_signal = ParsedSignal(
                        channel_id=channel_id,
                        message_id=str(message.id),
                        symbol=parsed_data.symbol,
                        direction=parsed_data.direction,
                        entry_price=parsed_data.entry_price,
                        stop_loss=parsed_data.stop_loss,
                        take_profit_1=parsed_data.take_profit_1,
                        take_profit_2=parsed_data.take_profit_2,
                        take_profit_3=parsed_data.take_profit_3,
                        risk_percentage=parsed_data.risk_percentage,
                        parsing_method=parsing_method,
                        confidence_score=parsed_data.confidence_score,
                        raw_message=message.text,
                        status="pending",
                        message_timestamp=message.date
                    )
                    db.add(parsed_signal)
                    db.commit()
                    
                    logger.info(
                        f"✓ Signal parsed: {channel.title} | "
                        f"{parsed_data.symbol} {parsed_data.direction} @ {parsed_data.entry_price} | "
                        f"Method: {parsing_method}"
                    )
                    
                else:
                    # Log parsing failure
                    log_entry = ExtractionLog(
                        channel_id=channel_id,
                        log_type="warning",
                        message=f"Failed to parse signal from message {message.id}",
                        log_metadata={
                            "message_text": message.text[:200],
                            "parsing_attempts": ["regex", "claude", "gemini", "openai"]
                        }
                    )
                    db.add(log_entry)
                    db.commit()
                    
                    logger.warning(f"✗ Failed to parse signal from {channel.title}")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                try:
                    log_entry = ExtractionLog(
                        channel_id=str(message.chat.id),
                        log_type="error",
                        message=f"Exception processing message: {str(e)}",
                        log_metadata={"error_type": type(e).__name__}
                    )
                    db.add(log_entry)
                    db.commit()
                except:
                    pass
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Critical error in process_message: {e}")
    
    async def stop_monitoring(self):
        """Stop monitoring channels"""
        self.is_running = False
        if self.client:
            try:
                await self.client.stop()
                logger.info("Telegram client stopped")
            except Exception as e:
                logger.error(f"Error stopping client: {e}")
    
    async def add_channel(self, channel_id: str, channel_name: str):
        """Add channel to monitoring list"""
        db = SessionLocal()
        try:
            # Check if channel already exists
            existing = db.query(TelegramChannel).filter(
                TelegramChannel.channel_id == channel_id
            ).first()
            
            if existing:
                existing.is_active = True
                logger.info(f"Channel {channel_name} re-activated")
            else:
                channel = TelegramChannel(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    is_active=True
                )
                db.add(channel)
                logger.info(f"Channel {channel_name} added to monitoring")
            
            db.commit()
            try:
                self.channels_to_monitor.append(int(channel_id))
            except:
                pass
            
        except Exception as e:
            logger.error(f"Failed to add channel: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def remove_channel(self, channel_id: str):
        """Remove channel from monitoring list"""
        db = SessionLocal()
        try:
            channel = db.query(TelegramChannel).filter(
                TelegramChannel.channel_id == channel_id
            ).first()
            
            if channel:
                channel.is_active = False
                db.commit()
                try:
                    if int(channel_id) in self.channels_to_monitor:
                        self.channels_to_monitor.remove(int(channel_id))
                except:
                    pass
                logger.info(f"Channel {channel.channel_name} removed from monitoring")
                
        except Exception as e:
            logger.error(f"Failed to remove channel: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def get_channel_stats(self, channel_id: str) -> dict:
        """Get extraction statistics for a channel"""
        db = SessionLocal()
        try:
            total = db.query(ParsedSignal).filter(
                ParsedSignal.channel_id == channel_id
            ).count()
            
            buy = db.query(ParsedSignal).filter(
                ParsedSignal.channel_id == channel_id,
                ParsedSignal.direction == "BUY"
            ).count()
            
            sell = db.query(ParsedSignal).filter(
                ParsedSignal.channel_id == channel_id,
                ParsedSignal.direction == "SELL"
            ).count()
            
            sent = db.query(ParsedSignal).filter(
                ParsedSignal.channel_id == channel_id,
                ParsedSignal.sent_to_supabase == True
            ).count()
            
            return {
                "total_signals": total,
                "buy_signals": buy,
                "sell_signals": sell,
                "sent_to_supabase": sent,
                "pending": total - sent
            }
            
        finally:
            db.close()

# Global instance
extractor = TelegramSignalExtractor()
