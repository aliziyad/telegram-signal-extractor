from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class SignalStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    MODIFIED = "modified"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class SignalActionType(str, Enum):
    NEW = "new"
    UPDATE = "update"
    MODIFY_SL = "modify_sl"
    MODIFY_TP = "modify_tp"
    CANCEL = "cancel"
    CLOSE = "close"
    PARTIAL_CLOSE = "partial_close"


class ParsingMethod(str, Enum):
    GEMINI = "gemini"
    CLAUDE = "claude"
    OPENAI = "openai"


# Channel Models
class ChannelBase(BaseModel):
    channel_id: str
    channel_name: str
    channel_username: Optional[str] = None
    channel_type: Optional[str] = None  # channel, supergroup, group


class ChannelCreate(ChannelBase):
    is_active: bool = True


class ChannelResponse(ChannelBase):
    id: str
    is_active: bool
    total_signals: int = 0
    sent_signals: int = 0
    pending_signals: int = 0
    failed_signals: int = 0
    created_at: datetime
    updated_at: datetime


class ChannelUpdate(BaseModel):
    is_active: Optional[bool] = None
    channel_name: Optional[str] = None


# Signal Models
class ParsedSignalData(BaseModel):
    symbol: str
    direction: SignalDirection
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    risk_percentage: Optional[float] = None
    lot_size: Optional[float] = None
    confidence_score: float = 1.0
    action_type: SignalActionType = SignalActionType.NEW
    original_signal_id: Optional[str] = None  # For modifications
    notes: Optional[str] = None


class SignalCreate(BaseModel):
    channel_id: str
    message_id: str
    raw_message: str
    parsed_data: Optional[ParsedSignalData] = None
    parsing_method: Optional[ParsingMethod] = None
    reply_to_message_id: Optional[str] = None
    message_timestamp: datetime


class SignalResponse(BaseModel):
    id: str
    channel_id: str
    message_id: str
    raw_message: str
    symbol: Optional[str] = None
    direction: Optional[str] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    action_type: str = "new"
    parsing_method: Optional[str] = None
    confidence_score: float = 1.0
    status: str = "pending"
    webhook_response: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None


# Telegram Auth Models
class TelegramAuthRequest(BaseModel):
    phone_number: str


class TelegramCodeVerify(BaseModel):
    phone_number: str
    code: str
    phone_code_hash: str


class TelegramPasswordVerify(BaseModel):
    password: str


# Session Status
class SessionStatus(BaseModel):
    is_connected: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    last_connected: Optional[datetime] = None
    error: Optional[str] = None


# Stats Models
class DashboardStats(BaseModel):
    total_signals: int = 0
    sent_signals: int = 0
    pending_signals: int = 0
    failed_signals: int = 0
    active_channels: int = 0
    total_channels: int = 0
    signals_today: int = 0
    success_rate: float = 0.0
    parsing_methods: List[Dict[str, Any]] = []
    is_monitoring: bool = False
    session_connected: bool = False


# Webhook Models
class WebhookPayload(BaseModel):
    channel_id: str
    channel_name: Optional[str] = None
    message_id: str
    raw_message: str
    timestamp: str
    action_type: str = "new"
    parsed_data: Dict[str, Any]
    original_signal_id: Optional[str] = None


# Log Models
class LogEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    log_type: str  # info, warning, error
    message: str
    channel_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Available Channel (from Telegram)
class AvailableChannel(BaseModel):
    channel_id: str
    channel_name: str
    channel_username: Optional[str] = None
    channel_type: str  # channel, supergroup, group
    members_count: Optional[int] = None
    is_already_monitored: bool = False
