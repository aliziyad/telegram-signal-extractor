import asyncio
import logging
import requests
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database.models import ParsedSignal
from app.database.connection import SessionLocal
from config.settings import settings
import json

logger = logging.getLogger(__name__)

class SignalSender:
    def __init__(self):
        self.session = requests.Session()
        self.is_running = False
        self.batch_size = settings.BATCH_SIZE
        
    async def start_sending_loop(self, interval: int = 5):
        """
        Start periodic sending of pending signals to Supabase
        
        Args:
            interval: Time in seconds between sending batches
        """
        self.is_running = True
        logger.info(f"🚀 Starting signal sender loop (interval: {interval}s)")
        
        try:
            while self.is_running:
                try:
                    await self.send_pending_signals()
                    await asyncio.sleep(interval)
                except Exception as e:
                    logger.error(f"Error in sending loop: {e}")
                    await asyncio.sleep(interval)
                    
        except asyncio.CancelledError:
            logger.info("Signal sender loop cancelled")
    
    async def send_pending_signals(self):
        """Send all pending signals to Supabase"""
        db = SessionLocal()
        try:
            # Get pending signals
            pending_signals = db.query(ParsedSignal).filter(
                ParsedSignal.status == "pending",
                ParsedSignal.sent_to_supabase == False
            ).limit(self.batch_size).all()
            
            if not pending_signals:
                logger.debug("No pending signals to send")
                return
            
            logger.info(f"📤 Sending {len(pending_signals)} signals to Supabase...")
            
            for signal in pending_signals:
                try:
                    success = await self.send_signal_to_supabase(signal, db)
                    if success:
                        signal.status = "sent"
                        signal.sent_to_supabase = True
                        signal.sent_at = datetime.utcnow()
                    else:
                        signal.status = "failed"
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Error sending signal {signal.id}: {e}")
                    signal.status = "failed"
                    signal.error_message = str(e)
                    db.commit()
            
        finally:
            db.close()
    
    async def send_signal_to_supabase(self, signal: ParsedSignal, db: Session) -> bool:
        """
        Send a single signal to Supabase API
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare payload
            payload = {
                "api_key": settings.COPY_SIGNAL_API_KEY,
                "channel_id": signal.channel_id,
                "raw_message": signal.raw_message,
                "timestamp": signal.message_timestamp.isoformat() if signal.message_timestamp else datetime.utcnow().isoformat(),
                "parsed_data": {
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "entry_price": signal.entry_price,
                    "stop_loss": signal.stop_loss,
                    "take_profit_1": signal.take_profit_1,
                    "take_profit_2": signal.take_profit_2,
                    "take_profit_3": signal.take_profit_3,
                    "risk_percentage": signal.risk_percentage,
                    "parsing_method": signal.parsing_method,
                    "confidence_score": signal.confidence_score
                }
            }
            
            # Send to Supabase
            response = self.session.post(
                settings.SUPABASE_INGEST_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.SUPABASE_API_KEY}"
                },
                timeout=settings.EXTRACTION_TIMEOUT
            )
            
            # Store response
            signal.supabase_response = {
                "status_code": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if response.status_code in [200, 201]:
                logger.info(
                    f"✓ Signal sent successfully: {signal.symbol} {signal.direction} "
                    f"(Signal ID: {signal.id}, HTTP: {response.status_code})"
                )
                return True
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"✗ Failed to send signal {signal.id}: {error_msg}")
                signal.error_message = error_msg
                return False
                
        except requests.Timeout:
            logger.error(f"Timeout sending signal {signal.id} to Supabase")
            signal.error_message = "Request timeout"
            return False
        except Exception as e:
            logger.error(f"Exception sending signal {signal.id}: {e}")
            signal.error_message = str(e)
            return False
    
    async def stop_sending(self):
        """Stop the sending loop"""
        self.is_running = False
        logger.info("Signal sender stopped")
    
    async def get_sending_stats(self) -> dict:
        """Get statistics about sent/pending signals"""
        db = SessionLocal()
        try:
            total = db.query(ParsedSignal).count()
            sent = db.query(ParsedSignal).filter(
                ParsedSignal.sent_to_supabase == True
            ).count()
            pending = db.query(ParsedSignal).filter(
                ParsedSignal.status == "pending"
            ).count()
            failed = db.query(ParsedSignal).filter(
                ParsedSignal.status == "failed"
            ).count()
            
            return {
                "total_signals": total,
                "sent": sent,
                "pending": pending,
                "failed": failed,
                "success_rate": (sent / total * 100) if total > 0 else 0
            }
            
        finally:
            db.close()

# Global instance
sender = SignalSender()
