import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz
from app.dashboard.routes import create_app
from app.extractors.telegram_client import extractor
from app.extractors.api_sender import sender
from app.database.connection import init_db
from config.settings import settings

# Configure logging
os.makedirs('logs', exist_ok=True)

log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# File handler
file_handler = RotatingFileHandler(
    settings.LOG_FILE,
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(log_formatter)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

# Root logger
root_logger = logging.getLogger()
root_logger.setLevel(settings.LOG_LEVEL)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)

class SignalExtractorService:
    def __init__(self):
        self.app = None
        self.scheduler = None
        self.telegram_task = None
        self.sender_task = None
        self.is_running = False
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("=" * 60)
        logger.info("🚀 Telegram Signal Extractor Service Starting")
        logger.info("=" * 60)
        
        try:
            # Initialize database
            logger.info("📦 Initializing database...")
            
            # Check if database reset is requested
            if os.getenv('RESET_DATABASE', '').lower() == 'true':
                logger.warning("⚠️  RESET_DATABASE=true detected - Resetting database schema...")
                from app.database.connection import reset_db
                reset_db()
                logger.info("✓ Database reset complete")
            else:
                init_db()
                logger.info("✓ Database initialized")
            
            # Create Flask app
            logger.info("🌐 Creating Flask application...")
            self.app = create_app()
            logger.info("✓ Flask app created")
            
            # Initialize Telegram client
            logger.info("📱 Initializing Telegram client...")
            await extractor.initialize()
            logger.info("✓ Telegram client initialized")
            
            # Initialize scheduler
            logger.info("⏰ Initializing scheduler...")
            self.scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
            self._setup_schedule()
            self.scheduler.start()
            logger.info("✓ Scheduler initialized")
            
            logger.info("=" * 60)
            logger.info("✅ Service initialized successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}", exc_info=True)
            raise
    
    def _setup_schedule(self):
        """Setup extraction schedule"""
        logger.info(f"📅 Schedule: {settings.SCHEDULE_START} - {settings.SCHEDULE_END} ({settings.TIMEZONE})")
        
        # Schedule extraction start
        self.scheduler.add_job(
            self.start_extraction,
            'cron',
            day_of_week='sun',
            hour=4,
            minute=0,
            timezone=settings.TIMEZONE,
            id='extraction_start'
        )
        
        # Schedule extraction stop
        self.scheduler.add_job(
            self.stop_extraction,
            'cron',
            day_of_week='fri',
            hour=22,
            minute=0,
            timezone=settings.TIMEZONE,
            id='extraction_stop'
        )
    
    async def start_extraction(self):
        """Start Telegram monitoring and signal sending"""
        logger.info("📌 Extraction window opened - Starting services...")
        
        if not self.is_running:
            self.is_running = True
            
            # Start Telegram monitoring
            self.telegram_task = asyncio.create_task(extractor.start_monitoring())
            logger.info("✓ Telegram monitoring started")
            
            # Start signal sender
            self.sender_task = asyncio.create_task(sender.start_sending_loop())
            logger.info("✓ Signal sender started")
    
    async def stop_extraction(self):
        """Stop Telegram monitoring and signal sending"""
        logger.info("🛑 Extraction window closed - Stopping services...")
        
        if self.is_running:
            self.is_running = False
            
            # Stop Telegram client
            await extractor.stop_monitoring()
            if self.telegram_task:
                self.telegram_task.cancel()
            logger.info("✓ Telegram monitoring stopped")
            
            # Stop signal sender
            await sender.stop_sending()
            if self.sender_task:
                self.sender_task.cancel()
            logger.info("✓ Signal sender stopped")
    
    async def run_flask_app(self):
        """Run Flask development server"""
        logger.info(f"🌍 Starting Flask server on {settings.FLASK_HOST}:{settings.FLASK_PORT}")
        
        # Import waitress for production-like serving
        from waitress import serve
        
        serve(
            self.app,
            host=settings.FLASK_HOST,
            port=settings.FLASK_PORT,
            threads=4
        )
    
    async def run(self):
        """Main service loop"""
        try:
            await self.initialize()
            
            # Check if we're in extraction window
            tz = pytz.timezone(settings.TIMEZONE)
            now = datetime.now(tz)
            start_hour = int(settings.SCHEDULE_START.split(':')[0])
            end_hour = int(settings.SCHEDULE_END.split(':')[0])
            
            # Simple check: if Monday-Friday between 4 AM - 10 PM
            is_extraction_window = (
                now.weekday() < 5 or (now.weekday() == 4 and now.hour < 22)
            ) and now.hour >= start_hour
            
            if is_extraction_window:
                logger.info("⏳ Currently in extraction window - starting services...")
                await self.start_extraction()
            else:
                logger.info("⏸️ Not in extraction window - services will start on next window")
            
            # Run Flask app in a thread-like manner
            import threading
            flask_thread = threading.Thread(target=self.run_flask_app, daemon=True)
            flask_thread.start()
            
            # Keep the async loop running
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n⏹️ Shutdown signal received")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("🧹 Cleaning up...")
        
        if self.is_running:
            await self.stop_extraction()
        
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
        
        logger.info("✅ Shutdown complete")

def main():
    """Entry point"""
    service = SignalExtractorService()
    
    # Run the service
    try:
        asyncio.run(service.run())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")

if __name__ == "__main__":
    main()
