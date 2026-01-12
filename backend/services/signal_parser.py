import os
import json
import logging
import asyncio
from typing import Optional, Tuple, Dict, Any
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
from backend.models.schemas import ParsedSignalData, SignalDirection, SignalActionType, ParsingMethod

load_dotenv()

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY", "")

SIGNAL_PARSING_PROMPT = """You are a trading signal parser. Analyze the following Telegram message and extract trading signal information.

IMPORTANT RULES:
1. If this is a NEW trading signal, extract: symbol, direction (BUY/SELL), entry price, stop loss, take profits
2. If this is an UPDATE/MODIFICATION to an existing signal, identify what's being changed:
   - "move SL to X" or "SL moved to X" = modify_sl action
   - "TP hit" or "take profit reached" = partial_close action
   - "cancel" or "cancelled" or "void" = cancel action  
   - "close" or "closed" or "exit" = close action
   - General update to entry/SL/TP = update action
3. If the message is NOT a trading signal (just chat, news, analysis without actionable trade), return null

Message to analyze:
{message}

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
    "is_signal": true/false,
    "symbol": "XAUUSD" or null,
    "direction": "BUY" or "SELL" or null,
    "entry_price": number or null,
    "stop_loss": number or null,
    "take_profit_1": number or null,
    "take_profit_2": number or null,
    "take_profit_3": number or null,
    "action_type": "new" or "update" or "modify_sl" or "modify_tp" or "cancel" or "close" or "partial_close",
    "confidence_score": 0.0 to 1.0,
    "notes": "brief explanation" or null
}}

If not a trading signal, return: {{"is_signal": false}}
"""

MODIFICATION_CONTEXT_PROMPT = """You are analyzing a REPLY message in a trading channel. The original message was a trading signal.

Original Signal:
{original_message}

Reply/Update Message:
{reply_message}

Determine what modification is being made to the original signal.

Return ONLY valid JSON:
{{
    "is_modification": true/false,
    "action_type": "update" or "modify_sl" or "modify_tp" or "cancel" or "close" or "partial_close",
    "new_stop_loss": number or null,
    "new_take_profit_1": number or null,
    "new_take_profit_2": number or null,
    "new_take_profit_3": number or null,
    "new_entry_price": number or null,
    "confidence_score": 0.0 to 1.0,
    "notes": "explanation of what changed"
}}
"""


class AISignalParser:
    """AI-powered signal parser using Gemini -> Claude -> OpenAI fallback"""
    
    def __init__(self):
        self.api_key = EMERGENT_LLM_KEY
        self.models = [
            ("gemini", "gemini-2.5-flash"),
            ("anthropic", "claude-4-sonnet-20250514"),
            ("openai", "gpt-4.1")
        ]
    
    async def parse_signal(self, message: str, is_reply: bool = False, original_message: str = None) -> Tuple[Optional[ParsedSignalData], Optional[ParsingMethod]]:
        """
        Parse a trading signal message using AI
        
        Args:
            message: The message text to parse
            is_reply: Whether this is a reply to another message
            original_message: The original message if this is a reply
            
        Returns:
            Tuple of (ParsedSignalData or None, ParsingMethod or None)
        """
        if not message or not message.strip():
            return None, None
        
        # Choose prompt based on context
        if is_reply and original_message:
            prompt = MODIFICATION_CONTEXT_PROMPT.format(
                original_message=original_message,
                reply_message=message
            )
        else:
            prompt = SIGNAL_PARSING_PROMPT.format(message=message)
        
        # Try each model in order
        for provider, model in self.models:
            try:
                result = await self._parse_with_model(provider, model, prompt, is_reply)
                if result:
                    method = ParsingMethod.GEMINI if provider == "gemini" else (
                        ParsingMethod.CLAUDE if provider == "anthropic" else ParsingMethod.OPENAI
                    )
                    logger.info(f"✅ Signal parsed successfully with {provider}/{model}")
                    return result, method
            except Exception as e:
                logger.warning(f"⚠️ {provider}/{model} parsing failed: {e}")
                continue
        
        logger.error(f"❌ All AI models failed to parse signal")
        return None, None
    
    async def _parse_with_model(self, provider: str, model: str, prompt: str, is_modification: bool = False) -> Optional[ParsedSignalData]:
        """Parse signal using specific AI model"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"signal-parser-{provider}",
                system_message="You are a precise trading signal parser. Return only valid JSON."
            ).with_model(provider, model)
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            # Clean and parse JSON response
            response_text = response.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            data = json.loads(response_text)
            
            # Check if it's a valid signal
            if is_modification:
                if not data.get("is_modification", False):
                    return None
                return self._build_modification_data(data)
            else:
                if not data.get("is_signal", False):
                    return None
                return self._build_signal_data(data)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error from {provider}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error with {provider}/{model}: {e}")
            raise
    
    def _build_signal_data(self, data: Dict[str, Any]) -> Optional[ParsedSignalData]:
        """Build ParsedSignalData from AI response"""
        try:
            direction = data.get("direction")
            entry_price = data.get("entry_price")
            
            if not direction or not entry_price:
                return None
            
            # Map action type
            action_str = data.get("action_type", "new").lower()
            action_map = {
                "new": SignalActionType.NEW,
                "update": SignalActionType.UPDATE,
                "modify_sl": SignalActionType.MODIFY_SL,
                "modify_tp": SignalActionType.MODIFY_TP,
                "cancel": SignalActionType.CANCEL,
                "close": SignalActionType.CLOSE,
                "partial_close": SignalActionType.PARTIAL_CLOSE
            }
            action_type = action_map.get(action_str, SignalActionType.NEW)
            
            return ParsedSignalData(
                symbol=data.get("symbol", "UNKNOWN"),
                direction=SignalDirection.BUY if direction.upper() == "BUY" else SignalDirection.SELL,
                entry_price=float(entry_price),
                stop_loss=float(data["stop_loss"]) if data.get("stop_loss") else None,
                take_profit_1=float(data["take_profit_1"]) if data.get("take_profit_1") else None,
                take_profit_2=float(data["take_profit_2"]) if data.get("take_profit_2") else None,
                take_profit_3=float(data["take_profit_3"]) if data.get("take_profit_3") else None,
                confidence_score=float(data.get("confidence_score", 0.9)),
                action_type=action_type,
                notes=data.get("notes")
            )
        except Exception as e:
            logger.error(f"Error building signal data: {e}")
            return None
    
    def _build_modification_data(self, data: Dict[str, Any]) -> Optional[ParsedSignalData]:
        """Build modification data from AI response"""
        try:
            action_str = data.get("action_type", "update").lower()
            action_map = {
                "update": SignalActionType.UPDATE,
                "modify_sl": SignalActionType.MODIFY_SL,
                "modify_tp": SignalActionType.MODIFY_TP,
                "cancel": SignalActionType.CANCEL,
                "close": SignalActionType.CLOSE,
                "partial_close": SignalActionType.PARTIAL_CLOSE
            }
            action_type = action_map.get(action_str, SignalActionType.UPDATE)
            
            return ParsedSignalData(
                symbol="",  # Will be filled from original signal
                direction=SignalDirection.BUY,  # Will be filled from original signal
                entry_price=float(data["new_entry_price"]) if data.get("new_entry_price") else 0,
                stop_loss=float(data["new_stop_loss"]) if data.get("new_stop_loss") else None,
                take_profit_1=float(data["new_take_profit_1"]) if data.get("new_take_profit_1") else None,
                take_profit_2=float(data["new_take_profit_2"]) if data.get("new_take_profit_2") else None,
                take_profit_3=float(data["new_take_profit_3"]) if data.get("new_take_profit_3") else None,
                confidence_score=float(data.get("confidence_score", 0.85)),
                action_type=action_type,
                notes=data.get("notes")
            )
        except Exception as e:
            logger.error(f"Error building modification data: {e}")
            return None


# Global parser instance
signal_parser = AISignalParser()
