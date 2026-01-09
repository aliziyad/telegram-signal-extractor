from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, Enum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class TelegramChannel(Base):
    __tablename__ = "telegram_channels"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(255), unique=True, nullable=False, index=True)
    channel_name = Column(String(255), nullable=False)
    channel_username = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    signals = relationship("ParsedSignal", back_populates="channel", cascade="all, delete-orphan")
    logs = relationship("ExtractionLog", back_populates="channel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TelegramChannel {self.channel_name}>"

class RawSignal(Base):
    __tablename__ = "raw_signals"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(255), ForeignKey("telegram_channels.channel_id"), nullable=False, index=True)
    message_id = Column(String(255), nullable=False, index=True)
    raw_message = Column(Text, nullable=False)
    message_timestamp = Column(DateTime, nullable=False, index=True)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RawSignal {self.message_id} from {self.channel_id}>"

class ParsedSignal(Base):
    __tablename__ = "parsed_signals"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(255), ForeignKey("telegram_channels.channel_id"), nullable=False, index=True)
    message_id = Column(String(255), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)  # e.g., XAUUSD
    direction = Column(String(10), nullable=False)  # BUY or SELL
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit_1 = Column(Float, nullable=True)
    take_profit_2 = Column(Float, nullable=True)
    take_profit_3 = Column(Float, nullable=True)
    risk_percentage = Column(Float, nullable=True)
    risk_reward_ratio = Column(Float, nullable=True)
    
    # Parsing metadata
    parsing_method = Column(String(50), nullable=False)  # regex, claude, gemini, openai
    confidence_score = Column(Float, default=1.0)
    raw_message = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)  # Store full parsed JSON
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, sent, failed
    sent_to_supabase = Column(Boolean, default=False)
    supabase_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    message_timestamp = Column(DateTime, nullable=False, index=True)
    extracted_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    channel = relationship("TelegramChannel", back_populates="signals")
    
    def __repr__(self):
        return f"<ParsedSignal {self.symbol} {self.direction} @ {self.entry_price}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "channel_id": self.channel_id,
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "take_profit_3": self.take_profit_3,
            "risk_percentage": self.risk_percentage,
            "risk_reward_ratio": self.risk_reward_ratio,
            "parsing_method": self.parsing_method,
            "confidence_score": self.confidence_score,
            "status": self.status,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
            "message_timestamp": self.message_timestamp.isoformat() if self.message_timestamp else None,
        }
    
    def to_supabase_payload(self):
        """Convert to Supabase API payload format"""
        return {
            "api_key": "",  # Will be set by sender
            "channel_id": self.channel_id,
            "raw_message": self.raw_message,
            "timestamp": self.message_timestamp.isoformat(),
            "parsed_data": self.to_dict()
        }

class ExtractionLog(Base):
    __tablename__ = "extraction_logs"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(255), ForeignKey("telegram_channels.channel_id"), nullable=True)
    log_type = Column(String(50), nullable=False, index=True)  # info, warning, error
    message = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    channel = relationship("TelegramChannel", back_populates="logs")
    
    def __repr__(self):
        return f"<ExtractionLog {self.log_type}: {self.message}>"

class ParsingError(Base):
    __tablename__ = "parsing_errors"
    
    id = Column(Integer, primary_key=True)
    raw_message = Column(Text, nullable=False)
    channel_id = Column(String(255), ForeignKey("telegram_channels.channel_id"), nullable=False, index=True)
    parsing_method = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    error_details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False)
    resolved_by_method = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<ParsingError {self.parsing_method} in {self.channel_id}>"

class SignalStats(Base):
    __tablename__ = "signal_stats"
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(255), ForeignKey("telegram_channels.channel_id"), nullable=False)
    date = Column(DateTime, nullable=False, index=True)
    total_signals = Column(Integer, default=0)
    buy_signals = Column(Integer, default=0)
    sell_signals = Column(Integer, default=0)
    parsing_success = Column(Integer, default=0)
    parsing_failed = Column(Integer, default=0)
    sent_to_supabase = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<SignalStats {self.channel_id} {self.date}>"
