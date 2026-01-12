import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# MongoDB connection - use localhost since MongoDB runs locally
MONGO_URL = os.getenv("MONGO_URL") or "mongodb://localhost:27017"
DATABASE_NAME = os.getenv("MONGO_DATABASE", "telegram_signals")

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
    """Create database indexes for better performance"""
    try:
        # Channels collection
        await async_db.channels.create_index("channel_id", unique=True)
        await async_db.channels.create_index("is_active")
        
        # Signals collection
        await async_db.signals.create_index("channel_id")
        await async_db.signals.create_index("message_id")
        await async_db.signals.create_index("status")
        await async_db.signals.create_index("created_at")
        await async_db.signals.create_index([("channel_id", 1), ("message_id", 1)], unique=True)
        
        # Raw messages collection
        await async_db.raw_messages.create_index("channel_id")
        await async_db.raw_messages.create_index("message_id")
        await async_db.raw_messages.create_index([("channel_id", 1), ("message_id", 1)], unique=True)
        
        # Session collection
        await async_db.sessions.create_index("session_name", unique=True)
        
        # Logs collection
        await async_db.logs.create_index("created_at")
        await async_db.logs.create_index("log_type")
        
        logger.info("✅ Database indexes created")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


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
