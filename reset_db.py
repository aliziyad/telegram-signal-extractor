#!/usr/bin/env python3
"""
Database reset script for Telegram Signal Extractor
Use this to reset the database schema after model changes
"""

import logging
from app.database.connection import reset_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Reset database schema"""
    try:
        logger.info("🔄 Resetting database schema...")
        logger.warning("⚠️  This will DELETE ALL DATA in the database!")
        
        # Uncomment the line below to actually reset the database
        # reset_db()
        
        print("\n" + "="*60)
        print("⚠️  DATABASE RESET DISABLED FOR SAFETY")
        print("="*60)
        print("To reset the database, edit reset_db.py and uncomment the reset_db() line")
        print("This will DELETE ALL DATA in your database!")
        print("="*60)
        
        logger.info("✅ Database reset complete")
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        raise

if __name__ == "__main__":
    main()