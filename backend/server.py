import os
import sys
import logging
import asyncio
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, '/app')

load_dotenv()

# Load auth config from environment
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
SECRET_KEY = os.environ.get("SECRET_KEY", "default-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

from backend.database.mongodb import connect_to_mongo, close_mongo_connection, get_database
from backend.services.telegram_client import telegram_client
from backend.services.notification_service import notification_service
from backend.models.schemas import (
    ChannelCreate, ChannelUpdate, ChannelResponse,
    SignalResponse, DashboardStats, SessionStatus,
    TelegramAuthRequest, TelegramCodeVerify, TelegramPasswordVerify,
    AvailableChannel
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background task reference
monitoring_task = None


async def auto_connect_telegram():
    """Background task to auto-connect to Telegram"""
    try:
        await asyncio.sleep(1)  # Small delay to let server start
        result = await telegram_client.connect()
        if result.get("success"):
            logger.info("✅ Auto-connected to Telegram")
            notification_service.set_client(telegram_client.client)
        else:
            logger.info(f"ℹ️ Auto-connect failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        logger.info(f"ℹ️ Auto-connect failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Telegram Signal Extractor...")
    await connect_to_mongo()
    
    # Try to auto-connect if session file exists (non-blocking)
    session_file = "/app/backend/sessions/signal_extractor.session"
    if os.path.exists(session_file):
        logger.info("📁 Session file found, will attempt auto-connect in background...")
        asyncio.create_task(auto_connect_telegram())
    else:
        logger.info("ℹ️ No session file found - use UI to connect")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await telegram_client.disconnect()
    await close_mongo_connection()


app = FastAPI(
    title="Telegram Signal Extractor API",
    description="Extract and process trading signals from Telegram channels",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Auth Models ====================

class LoginRequest(BaseModel):
    username: str
    password: str


# ==================== Auth Routes ====================

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Admin login endpoint"""
    if request.username == ADMIN_USERNAME and request.password == ADMIN_PASSWORD:
        # Generate JWT token
        payload = {
            "sub": request.username,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)
        return {
            "success": True,
            "token": token,
            "username": request.username,
            "expires_in": JWT_EXPIRY_HOURS * 3600
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/auth/verify")
async def verify_token(token: str = None):
    """Verify JWT token validity"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {"valid": True, "username": payload.get("sub")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ==================== Health Check ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "telegram-signal-extractor"
    }


# ==================== Session/Auth Routes ====================

@app.get("/api/session/status", response_model=dict)
async def get_session_status():
    """Get current Telegram session status"""
    return await telegram_client.get_session_status()


@app.post("/api/session/send-code")
async def send_verification_code(request: TelegramAuthRequest):
    """Send verification code to phone number"""
    result = await telegram_client.send_code(request.phone_number)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send code"))
    return result


@app.post("/api/session/verify-code")
async def verify_code(request: TelegramCodeVerify):
    """Verify the authentication code"""
    result = await telegram_client.verify_code(
        request.phone_number,
        request.code,
        request.phone_code_hash
    )
    if not result.get("success") and not result.get("needs_password"):
        raise HTTPException(status_code=400, detail=result.get("error", "Verification failed"))
    return result


@app.post("/api/session/verify-password")
async def verify_password(request: TelegramPasswordVerify):
    """Verify 2FA password"""
    result = await telegram_client.verify_password(request.password)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Password verification failed"))
    return result


@app.post("/api/session/connect")
async def connect_session():
    """Connect to existing Telegram session"""
    result = await telegram_client.connect()
    if result.get("success"):
        notification_service.set_client(telegram_client.client)
    return result


@app.post("/api/session/disconnect")
async def disconnect_session():
    """Disconnect from Telegram"""
    global monitoring_task
    if monitoring_task:
        monitoring_task.cancel()
        monitoring_task = None
    await telegram_client.disconnect()
    return {"success": True, "message": "Disconnected"}


# ==================== Channel Routes ====================

@app.get("/api/channels/available", response_model=List[AvailableChannel])
async def get_available_channels():
    """Get all channels/groups the user is subscribed to"""
    if not telegram_client.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to Telegram")
    return await telegram_client.get_available_channels()


@app.get("/api/channels")
async def get_monitored_channels():
    """Get all monitored channels with stats"""
    db = get_database()
    channels = await db.channels.find().to_list(1000)
    
    result = []
    for channel in channels:
        # Get stats for each channel
        channel_id = channel["channel_id"]
        
        total = await db.signals.count_documents({"channel_id": channel_id})
        sent = await db.signals.count_documents({"channel_id": channel_id, "status": "sent"})
        pending = await db.signals.count_documents({"channel_id": channel_id, "status": "pending"})
        failed = await db.signals.count_documents({"channel_id": channel_id, "status": "failed"})
        
        result.append({
            "id": str(channel["_id"]),
            "channel_id": channel["channel_id"],
            "channel_name": channel["channel_name"],
            "channel_username": channel.get("channel_username"),
            "channel_type": channel.get("channel_type"),
            "is_active": channel.get("is_active", True),
            "total_signals": total,
            "sent_signals": sent,
            "pending_signals": pending,
            "failed_signals": failed,
            "created_at": channel.get("created_at", datetime.utcnow()).isoformat(),
            "updated_at": channel.get("updated_at", datetime.utcnow()).isoformat()
        })
    
    return result


@app.post("/api/channels")
async def add_channel(channel: ChannelCreate):
    """Add a channel to monitor"""
    if not telegram_client.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to Telegram")
    
    success = await telegram_client.add_channel_to_monitor(
        channel.channel_id,
        channel.channel_name,
        channel.channel_username,
        channel.channel_type
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add channel")
    
    return {"success": True, "message": f"Channel {channel.channel_name} added"}


@app.put("/api/channels/{channel_id}")
async def update_channel(channel_id: str, update: ChannelUpdate):
    """Update channel (toggle active status)"""
    db = get_database()
    
    update_data = {"updated_at": datetime.utcnow()}
    if update.is_active is not None:
        update_data["is_active"] = update.is_active
        
        # Update telegram client's monitored list
        if update.is_active:
            if int(channel_id) not in telegram_client.monitored_channels:
                telegram_client.monitored_channels.append(int(channel_id))
        else:
            if int(channel_id) in telegram_client.monitored_channels:
                telegram_client.monitored_channels.remove(int(channel_id))
    
    if update.channel_name:
        update_data["channel_name"] = update.channel_name
    
    result = await db.channels.update_one(
        {"channel_id": channel_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return {"success": True, "message": "Channel updated"}


@app.delete("/api/channels/{channel_id}")
async def delete_channel(channel_id: str):
    """Delete a channel from monitoring"""
    db = get_database()
    
    # Remove from monitoring
    await telegram_client.remove_channel_from_monitor(channel_id)
    
    # Delete from database
    result = await db.channels.delete_one({"channel_id": channel_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return {"success": True, "message": "Channel deleted"}


# ==================== Monitoring Routes ====================

@app.post("/api/monitoring/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start monitoring channels for signals"""
    global monitoring_task
    
    if not telegram_client.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to Telegram")
    
    if telegram_client.is_monitoring:
        return {"success": True, "message": "Already monitoring"}
    
    # Start monitoring in background
    monitoring_task = asyncio.create_task(telegram_client.start_monitoring())
    
    return {"success": True, "message": "Monitoring started"}


@app.post("/api/monitoring/stop")
async def stop_monitoring():
    """Stop monitoring channels"""
    global monitoring_task
    
    await telegram_client.stop_monitoring()
    
    if monitoring_task:
        monitoring_task.cancel()
        monitoring_task = None
    
    return {"success": True, "message": "Monitoring stopped"}


@app.get("/api/monitoring/status")
async def get_monitoring_status():
    """Get monitoring status"""
    return {
        "is_monitoring": telegram_client.is_monitoring,
        "is_connected": telegram_client.is_connected,
        "monitored_channels": len(telegram_client.monitored_channels)
    }


# ==================== Signal Routes ====================

@app.get("/api/signals")
async def get_signals(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    channel_id: Optional[str] = None
):
    """Get signals with pagination and filters"""
    db = get_database()
    
    # Build query
    query = {}
    if status:
        query["status"] = status
    if channel_id:
        query["channel_id"] = channel_id
    
    # Get total count
    total = await db.signals.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * limit
    signals = await db.signals.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    result = []
    for signal in signals:
        result.append({
            "id": str(signal["_id"]),
            "channel_id": signal["channel_id"],
            "channel_name": signal.get("channel_name", "Unknown"),
            "message_id": signal["message_id"],
            "raw_message": signal.get("raw_message", ""),
            "symbol": signal.get("symbol"),
            "direction": signal.get("direction"),
            "entry_price": signal.get("entry_price"),
            "stop_loss": signal.get("stop_loss"),
            "take_profit_1": signal.get("take_profit_1"),
            "take_profit_2": signal.get("take_profit_2"),
            "take_profit_3": signal.get("take_profit_3"),
            "action_type": signal.get("action_type", "new"),
            "parsing_method": signal.get("parsing_method"),
            "confidence_score": signal.get("confidence_score", 1.0),
            "status": signal.get("status", "pending"),
            "error_message": signal.get("error_message"),
            "created_at": signal.get("created_at", datetime.utcnow()).isoformat(),
            "sent_at": signal.get("sent_at").isoformat() if signal.get("sent_at") else None
        })
    
    return {
        "signals": result,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


# ==================== Stats Routes ====================

@app.get("/api/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    db = get_database()
    
    # Signal stats
    total_signals = await db.signals.count_documents({})
    sent_signals = await db.signals.count_documents({"status": "sent"})
    pending_signals = await db.signals.count_documents({"status": "pending"})
    failed_signals = await db.signals.count_documents({"status": "failed"})
    
    # Channel stats
    total_channels = await db.channels.count_documents({})
    active_channels = await db.channels.count_documents({"is_active": True})
    
    # Today's signals
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    signals_today = await db.signals.count_documents({"created_at": {"$gte": today_start}})
    
    # Parsing methods breakdown
    pipeline = [
        {"$group": {"_id": "$parsing_method", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    methods_cursor = db.signals.aggregate(pipeline)
    parsing_methods = []
    async for method in methods_cursor:
        if method["_id"]:
            parsing_methods.append({
                "method": method["_id"],
                "count": method["count"]
            })
    
    # Success rate
    success_rate = (sent_signals / total_signals * 100) if total_signals > 0 else 0
    
    return DashboardStats(
        total_signals=total_signals,
        sent_signals=sent_signals,
        pending_signals=pending_signals,
        failed_signals=failed_signals,
        active_channels=active_channels,
        total_channels=total_channels,
        signals_today=signals_today,
        success_rate=round(success_rate, 2),
        parsing_methods=parsing_methods,
        is_monitoring=telegram_client.is_monitoring,
        session_connected=telegram_client.is_connected
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
