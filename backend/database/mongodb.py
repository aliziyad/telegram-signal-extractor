import os
import logging
from urllib.parse import urlparse
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def extract_db_name_from_url(mongo_url: str) -> str:
    """Extract database name from MongoDB connection string"""
    try:
        # Parse the URL
        parsed = urlparse(mongo_url)
        
        # Get the path (database name is after the /)
        path = parsed.path
        if path and path.startswith('/'):
            path = path[1:]
        
        # Remove any query parameters from the path
        if '?' in path:
            path = path.split('?')[0]
        
        # If we have a database name in the path, use it
        if path and path != '':
            return path
        
        # Otherwise return default
        return "telegram_signals"
    except Exception as e:
        logger.warning(f"Could not parse database name from URL: {e}")
        return "telegram_signals"


# MongoDB connection - extract database name from URL for Atlas compatibility
MONGO_URL = os.getenv("MONGO_URL") or "mongodb://localhost:27017"

# First check for explicit MONGO_DATABASE env var, then extract from URL
_explicit_db = os.getenv("MONGO_DATABASE") or os.getenv("DB_NAME")
if _explicit_db:
    DATABASE_NAME = _explicit_db
else:
    DATABASE_NAME = extract_db_name_from_url(MONGO_URL)

logger.info(f"Using MongoDB database: {DATABASE_NAME}")

# Async client for FastAPI
async_client = None
async_db = None

# Sync client for background tasks
sync_client = None
sync_db = None


async def connect_to_mongo():
    """Connect to MongoDB (async)"""
    global async_client, async_db
    try:
        async_client = AsyncIOMotorClient(MONGO_URL)
        async_db = async_client[DATABASE_NAME]
        # Test connection
        await async_client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {DATABASE_NAME}")
        
        # Create indexes
        await create_indexes()
        
        return async_db
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise


async def create_indexes():
    """Create database indexes for better performance (non-blocking on errors)"""
    try:
        # Channels collection
        try:
            await async_db.channels.create_index("channel_id", unique=True)
            await async_db.channels.create_index("is_active")
        except Exception as e:
            logger.debug(f"Channel indexes may already exist or not authorized: {e}")
        
        # Signals collection
        try:
            await async_db.signals.create_index("channel_id")
            await async_db.signals.create_index("message_id")
            await async_db.signals.create_index("status")
            await async_db.signals.create_index("created_at")
            await async_db.signals.create_index([("channel_id", 1), ("message_id", 1)], unique=True)
        except Exception as e:
            logger.debug(f"Signal indexes may already exist or not authorized: {e}")
        
        # Raw messages collection
        try:
            await async_db.raw_messages.create_index("channel_id")
            await async_db.raw_messages.create_index("message_id")
            await async_db.raw_messages.create_index([("channel_id", 1), ("message_id", 1)], unique=True)
        except Exception as e:
            logger.debug(f"Raw message indexes may already exist or not authorized: {e}")
        
        # Session collection
        try:
            await async_db.sessions.create_index("session_name", unique=True)
        except Exception as e:
            logger.debug(f"Session indexes may already exist or not authorized: {e}")
        
        # Logs collection
        try:
            await async_db.logs.create_index("created_at")
            await async_db.logs.create_index("log_type")
        except Exception as e:
            logger.debug(f"Log indexes may already exist or not authorized: {e}")
        
        logger.info("✅ Database indexes created/verified")
    except Exception as e:
        logger.warning(f"Index creation warning (non-fatal): {e}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global async_client
    if async_client:
        async_client.close()
        logger.info("MongoDB connection closed")


def get_sync_db():
    """Get sync MongoDB client for background tasks"""
    global sync_client, sync_db
    if sync_client is None:
        sync_client = MongoClient(MONGO_URL)
        sync_db = sync_client[DATABASE_NAME]
    return sync_db


def get_database():
    """Get async database instance"""
    return async_db


# Collections helper
class Collections:
    @staticmethod
    def channels():
        return async_db.channels
    
    @staticmethod
    def signals():
        return async_db.signals
    
    @staticmethod
    def raw_messages():
        return async_db.raw_messages
    
    @staticmethod
    def sessions():
        return async_db.sessions
    
    @staticmethod
    def logs():
        return async_db.logs
    
    @staticmethod
    def stats():
        return async_db.stats
