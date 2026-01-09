import regex as re
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from anthropic import Anthropic
from google.generativeai import GenerativeModel
from openai import OpenAI
from config.settings import settings

logger = logging.getLogger(__name__)

class ParsingMethod(str, Enum):
    REGEX = "regex"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"

@dataclass
class ParsedSignalData:
    symbol: str
    direction: str  # BUY or SELL
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    risk_percentage: Optional[float] = None
    confidence_score: float = 1.0
    parsing_method: str = "unknown"

class SignalParser:
    def __init__(self):
        self.claude_client = None
        self.gemini_client = None
        self.openai_client = None
        
        if settings.CLAUDE_ENABLED and settings.CLAUDE_API_KEY:
            self.claude_client = Anthropic(api_key=settings.CLAUDE_API_KEY)
        
        if settings.GEMINI_ENABLED and settings.GEMINI_API_KEY:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.gemini_client = genai
        
        if settings.OPENAI_ENABLED and settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def parse_signal(self, raw_message: str, channel_name: str = "") -> tuple[Optional[ParsedSignalData], str]:
        """
        Parse raw signal message using priority order: regex -> Claude -> Gemini -> OpenAI
        Returns: (ParsedSignalData, parsing_method) or (None, failed_method)
        """
        logger.info(f"Parsing signal from {channel_name}: {raw_message[:100]}...")
        
        # Try regex first (fastest, no API calls)
        if settings.REGEX_ENABLED:
            try:
                parsed = self._parse_with_regex(raw_message)
                if parsed:
                    logger.info(f"✓ Regex parsing successful for {parsed.symbol} {parsed.direction}")
                    parsed.parsing_method = ParsingMethod.REGEX
                    return parsed, ParsingMethod.REGEX
            except Exception as e:
                logger.warning(f"Regex parsing failed: {e}")
        
        # Fall back to AI APIs
        for method in settings.PARSING_PRIORITY[1:]:  # Skip regex since we tried it
            if method == ParsingMethod.CLAUDE and settings.CLAUDE_ENABLED:
                try:
                    parsed = self._parse_with_claude(raw_message)
                    if parsed:
                        logger.info(f"✓ Claude parsing successful for {parsed.symbol} {parsed.direction}")
                        parsed.parsing_method = ParsingMethod.CLAUDE
                        parsed.confidence_score = 0.95
                        return parsed, ParsingMethod.CLAUDE
                except Exception as e:
                    logger.warning(f"Claude parsing failed: {e}")
            
            elif method == ParsingMethod.GEMINI and settings.GEMINI_ENABLED:
                try:
                    parsed = self._parse_with_gemini(raw_message)
                    if parsed:
                        logger.info(f"✓ Gemini parsing successful for {parsed.symbol} {parsed.direction}")
                        parsed.parsing_method = ParsingMethod.GEMINI
                        parsed.confidence_score = 0.90
                        return parsed, ParsingMethod.GEMINI
                except Exception as e:
                    logger.warning(f"Gemini parsing failed: {e}")
            
            elif method == ParsingMethod.OPENAI and settings.OPENAI_ENABLED:
                try:
                    parsed = self._parse_with_openai(raw_message)
                    if parsed:
                        logger.info(f"✓ OpenAI parsing successful for {parsed.symbol} {parsed.direction}")
                        parsed.parsing_method = ParsingMethod.OPENAI
                        parsed.confidence_score = 0.92
                        return parsed, ParsingMethod.OPENAI
                except Exception as e:
                    logger.warning(f"OpenAI parsing failed: {e}")
        
        logger.error(f"All parsing methods failed for message: {raw_message[:100]}")
        return None, "all_methods_failed"
    
    def _parse_with_regex(self, message: str) -> Optional[ParsedSignalData]:
        """Parse signal using regex patterns"""
        message_upper = message.upper()
        
        # Detect symbol (primarily XAUUSD, but support others)
        symbol_pattern = r'\b(XAUUSD|EURUSD|GBPUSD|AUDUSD|USDJPY|GOLD|FOREX)\b'
        symbol_match = re.search(symbol_pattern, message_upper)
        symbol = symbol_match.group(1) if symbol_match else "XAUUSD"
        
        # Detect direction
        buy_pattern = r'\b(BUY|LONG|BULLISH|COMPRAR|ACHETER)\b'
        sell_pattern = r'\b(SELL|SHORT|BEARISH|VENDRE|VENDER)\b'
        
        buy_match = re.search(buy_pattern, message_upper)
        sell_match = re.search(sell_pattern, message_upper)
        
        if buy_match:
            direction = "BUY"
        elif sell_match:
            direction = "SELL"
        else:
            raise ValueError("Could not determine BUY/SELL direction")
        
        # Extract prices - more flexible patterns
        # Entry price patterns: ENTRY, ENTER, BUY @, SELL @, @ symbol
        entry_pattern = r'(?:ENTRY|ENTER|BUY|SELL|@)\s*:?\s*(\d+\.?\d*)'
        entry_matches = re.findall(entry_pattern, message_upper)
        
        if not entry_matches:
            raise ValueError("Could not extract entry price")
        
        # Use first match as entry price (often entry is mentioned first)
        entry_price = float(entry_matches[0])
        
        # Extract stop loss
        sl_pattern = r'(?:SL|STOPLOSS|STOP\s*LOSS)\s*:?\s*(\d+\.?\d*)'
        sl_match = re.search(sl_pattern, message_upper)
        stop_loss = float(sl_match.group(1)) if sl_match else None
        
        # Extract take profits (TP, TP1, TP2, TP3, TARGET)
        tp_patterns = {
            'tp1': r'(?:TP\s*1|TP1|TARGET\s*1)\s*:?\s*(\d+\.?\d*)',
            'tp2': r'(?:TP\s*2|TP2|TARGET\s*2)\s*:?\s*(\d+\.?\d*)',
            'tp3': r'(?:TP\s*3|TP3|TARGET\s*3)\s*:?\s*(\d+\.?\d*)',
        }
        
        take_profits = {}
        for tp_name, pattern in tp_patterns.items():
            tp_match = re.search(pattern, message_upper)
            if tp_match:
                take_profits[tp_name] = float(tp_match.group(1))
        
        # Calculate risk if we have SL and entry
        risk_percentage = None
        if stop_loss and entry_price:
            risk_percentage = abs((entry_price - stop_loss) / entry_price * 100)
        
        return ParsedSignalData(
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profits.get('tp1'),
            take_profit_2=take_profits.get('tp2'),
            take_profit_3=take_profits.get('tp3'),
            risk_percentage=risk_percentage,
            parsing_method=ParsingMethod.REGEX
        )
    
    def _parse_with_claude(self, message: str) -> Optional[ParsedSignalData]:
        """Parse signal using Claude API"""
        if not self.claude_client:
            raise ValueError("Claude client not initialized")
        
        prompt = f"""Extract trading signal information from this message and return ONLY valid JSON.

Message: {message}

Return JSON format (all numeric values as numbers, not strings):
{{
    "symbol": "XAUUSD",
    "direction": "BUY" or "SELL",
    "entry_price": number,
    "stop_loss": number or null,
    "take_profit_1": number or null,
    "take_profit_2": number or null,
    "take_profit_3": number or null,
    "risk_percentage": number or null
}}

If direction or entry price cannot be determined, return null.
Return ONLY the JSON object, no other text."""
        
        try:
            response = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = response.content[0].text.strip()
            # Clean JSON response
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(response_text)
            
            if not data.get("direction") or not data.get("entry_price"):
                return None
            
            return ParsedSignalData(
                symbol=data.get("symbol", "XAUUSD"),
                direction=data["direction"],
                entry_price=data["entry_price"],
                stop_loss=data.get("stop_loss"),
                take_profit_1=data.get("take_profit_1"),
                take_profit_2=data.get("take_profit_2"),
                take_profit_3=data.get("take_profit_3"),
                risk_percentage=data.get("risk_percentage"),
                parsing_method=ParsingMethod.CLAUDE
            )
        except Exception as e:
            logger.error(f"Claude parsing error: {e}")
            raise
    
    def _parse_with_gemini(self, message: str) -> Optional[ParsedSignalData]:
        """Parse signal using Google Gemini API"""
        if not self.gemini_client:
            raise ValueError("Gemini client not initialized")
        
        model = self.gemini_client.GenerativeModel('gemini-pro')
        
        prompt = f"""Extract trading signal information from this message and return ONLY valid JSON.

Message: {message}

Return JSON format (all numeric values as numbers, not strings):
{{
    "symbol": "XAUUSD",
    "direction": "BUY" or "SELL",
    "entry_price": number,
    "stop_loss": number or null,
    "take_profit_1": number or null,
    "take_profit_2": number or null,
    "take_profit_3": number or null,
    "risk_percentage": number or null
}}

Return ONLY the JSON object, no other text."""
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(response_text)
            
            if not data.get("direction") or not data.get("entry_price"):
                return None
            
            return ParsedSignalData(
                symbol=data.get("symbol", "XAUUSD"),
                direction=data["direction"],
                entry_price=data["entry_price"],
                stop_loss=data.get("stop_loss"),
                take_profit_1=data.get("take_profit_1"),
                take_profit_2=data.get("take_profit_2"),
                take_profit_3=data.get("take_profit_3"),
                risk_percentage=data.get("risk_percentage"),
                parsing_method=ParsingMethod.GEMINI
            )
        except Exception as e:
            logger.error(f"Gemini parsing error: {e}")
            raise
    
    def _parse_with_openai(self, message: str) -> Optional[ParsedSignalData]:
        """Parse signal using OpenAI API"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        prompt = f"""Extract trading signal information from this message and return ONLY valid JSON.

Message: {message}

Return JSON format (all numeric values as numbers, not strings):
{{
    "symbol": "XAUUSD",
    "direction": "BUY" or "SELL",
    "entry_price": number,
    "stop_loss": number or null,
    "take_profit_1": number or null,
    "take_profit_2": number or null,
    "take_profit_3": number or null,
    "risk_percentage": number or null
}}

Return ONLY the JSON object, no other text."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(response_text)
            
            if not data.get("direction") or not data.get("entry_price"):
                return None
            
            return ParsedSignalData(
                symbol=data.get("symbol", "XAUUSD"),
                direction=data["direction"],
                entry_price=data["entry_price"],
                stop_loss=data.get("stop_loss"),
                take_profit_1=data.get("take_profit_1"),
                take_profit_2=data.get("take_profit_2"),
                take_profit_3=data.get("take_profit_3"),
                risk_percentage=data.get("risk_percentage"),
                parsing_method=ParsingMethod.OPENAI
            )
        except Exception as e:
            logger.error(f"OpenAI parsing error: {e}")
            raise
