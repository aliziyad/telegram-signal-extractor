# Webhook API Documentation

## Overview
This document describes the webhook payload format that the Telegram Signal Extractor sends to external systems when a trading signal is captured.

## Endpoint Requirements

Your external system needs to implement a POST endpoint that accepts the following:

### Request

**Method:** `POST`

**Headers:**
```
Content-Type: application/json
Authorization: Bearer <API_KEY>
x-api-key: <API_KEY>
```

### Request Body (JSON)

```json
{
  "channel_telegram_id": "-1002828126112",
  "channel_name": "Profit King",
  "channel_username": "profit_king_ea",
  "message_id": "69",
  "raw_message": "🔤🔤🔤🔤🔤🔤🔤🔤\n\n♾️GOLD BUY NOW @ 4555.5\n\n💰TP 1: 4569.8\n💰TP 2: 4571.3\n💰TP 3: 4574.3/OPEN\n\n🚨SL: 4543.3",
  "timestamp": "2026-01-12T20:22:54.678000",
  "action_type": "new",
  "parsed_signal": {
    "symbol": "XAUUSD",
    "direction": "BUY",
    "entry_price": 4555.5,
    "stop_loss": 4543.3,
    "take_profit_1": 4569.8,
    "take_profit_2": 4571.3,
    "take_profit_3": 4574.3,
    "confidence_score": 1.0,
    "parsing_method": "gemini",
    "notes": null
  },
  "original_signal_id": null
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `channel_telegram_id` | string | **Telegram channel ID** - Use this to match signals to specific channels |
| `channel_name` | string | Display name of the Telegram channel |
| `channel_username` | string | Telegram @username of the channel (may be null) |
| `message_id` | string | Unique message ID within the channel |
| `raw_message` | string | Original unprocessed message text from Telegram |
| `timestamp` | string | ISO 8601 timestamp when the message was received |
| `action_type` | string | Type of signal action (see below) |
| `parsed_signal` | object | AI-parsed signal data |
| `original_signal_id` | string | For modifications, the ID of the original signal |

### Action Types

| Action | Description |
|--------|-------------|
| `new` | New trading signal |
| `update` | General update to an existing signal |
| `modify_sl` | Stop loss modification |
| `modify_tp` | Take profit modification |
| `cancel` | Signal cancelled/voided |
| `close` | Signal closed/exit position |
| `partial_close` | Partial position closed |

### Parsed Signal Object

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Trading symbol (e.g., "XAUUSD", "EURUSD") |
| `direction` | string | "BUY" or "SELL" |
| `entry_price` | number | Entry price for the trade |
| `stop_loss` | number | Stop loss level (may be null) |
| `take_profit_1` | number | First take profit level (may be null) |
| `take_profit_2` | number | Second take profit level (may be null) |
| `take_profit_3` | number | Third take profit level (may be null) |
| `confidence_score` | number | AI confidence score 0.0-1.0 |
| `parsing_method` | string | "gemini", "claude", or "openai" |
| `notes` | string | Additional notes from AI parsing (may be null) |

## Expected Response

### Success Response
```json
{
  "success": true,
  "message": "Signal received"
}
```
**HTTP Status:** 200, 201, or 202

### Error Response
```json
{
  "success": false,
  "error": "Error description"
}
```
**HTTP Status:** 4xx or 5xx

## Example Implementation (Node.js/Express)

```javascript
app.post('/webhook/signals', (req, res) => {
  const apiKey = req.headers['x-api-key'] || req.headers['authorization']?.replace('Bearer ', '');
  
  // Validate API key
  if (apiKey !== process.env.EXPECTED_API_KEY) {
    return res.status(401).json({ success: false, error: 'Unauthorized' });
  }
  
  const {
    channel_telegram_id,
    channel_name,
    message_id,
    raw_message,
    timestamp,
    action_type,
    parsed_signal,
    original_signal_id
  } = req.body;
  
  // Validate required fields
  if (!channel_telegram_id || !raw_message || !parsed_signal) {
    return res.status(400).json({ 
      success: false, 
      error: 'Missing required fields: channel_telegram_id, raw_message, or parsed_signal' 
    });
  }
  
  // Process the signal based on channel_telegram_id
  // Your logic here...
  
  console.log(`Signal from ${channel_name} (${channel_telegram_id}): ${parsed_signal.symbol} ${parsed_signal.direction}`);
  
  res.json({ success: true, message: 'Signal received' });
});
```

## Example Implementation (Python/FastAPI)

```python
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

class ParsedSignal(BaseModel):
    symbol: str
    direction: str
    entry_price: float
    stop_loss: Optional[float]
    take_profit_1: Optional[float]
    take_profit_2: Optional[float]
    take_profit_3: Optional[float]
    confidence_score: float
    parsing_method: str
    notes: Optional[str]

class SignalWebhook(BaseModel):
    channel_telegram_id: str
    channel_name: str
    channel_username: Optional[str]
    message_id: str
    raw_message: str
    timestamp: str
    action_type: str
    parsed_signal: ParsedSignal
    original_signal_id: Optional[str]

app = FastAPI()

@app.post("/webhook/signals")
async def receive_signal(
    signal: SignalWebhook,
    x_api_key: str = Header(None),
    authorization: str = Header(None)
):
    api_key = x_api_key or (authorization.replace("Bearer ", "") if authorization else None)
    
    if api_key != "YOUR_EXPECTED_API_KEY":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Process signal based on channel_telegram_id
    print(f"Signal from {signal.channel_name} ({signal.channel_telegram_id})")
    print(f"{signal.parsed_signal.symbol} {signal.parsed_signal.direction} @ {signal.parsed_signal.entry_price}")
    
    return {"success": True, "message": "Signal received"}
```

## Channel ID Matching

The `channel_telegram_id` field is the key identifier for matching signals to channels in your system. 

**Example channel IDs from the monitored channels:**
- `-1002828126112` - Profit King
- `-1001222394814` - Maestro Fx
- `-1002884310898` - Rasmi Trade

Use this ID in your external system to route signals to the appropriate handlers or display them in the correct context.
