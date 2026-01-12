# Telegram Signal Extractor - Product Requirements Document

## Overview
A comprehensive system that connects to a user's Telegram account, monitors selected channels for trading signals, parses them using AI (Gemini → Claude → OpenAI fallback), and sends extracted signals to an external webhook endpoint.

## Core Features

### 1. Telegram Session Management
- **Connect/Disconnect**: Secure authentication flow with phone number verification
- **2FA Support**: Handle two-factor authentication if enabled
- **Session Persistence**: Maintain session across restarts using pyrogram sessions
- **Disconnection Alerts**: Send Telegram notifications to admin when session disconnects

### 2. Channel Management
- **Auto-Discovery**: Extract all channels, supergroups, and groups the user is subscribed to
- **Selective Monitoring**: Add/remove channels from monitoring list
- **Channel Stats**: Track signals extracted per channel

### 3. Signal Extraction
- **Real-time Monitoring**: Listen for new messages in monitored channels
- **AI-Powered Parsing**: Parse signals using:
  - Primary: Google Gemini (gemini-2.5-flash)
  - Fallback 1: Claude (claude-4-sonnet)
  - Fallback 2: OpenAI (gpt-4.1)
- **Signal Data Extracted**:
  - Symbol (e.g., XAUUSD, EURUSD)
  - Direction (BUY/SELL)
  - Entry Price
  - Stop Loss
  - Take Profit 1/2/3
  - Confidence Score
  - Action Type

### 4. Signal Modifications
- **Edit Detection**: Detect when original signal messages are edited
- **Reply Parsing**: Parse reply messages for modifications:
  - Move SL (Stop Loss updates)
  - Cancel trade
  - Close trade
  - Partial close
  - General updates

### 5. Webhook Integration
- **External Webhook**: Send signals to lovable.dev endpoint
- **Webhook URL**: https://zcdggtjwrtrqhqrngfau.supabase.co/functions/v1/fastsignal-webhook
- **Payload Format**: JSON with channel_id, parsed_data, timestamps

### 6. Dashboard
- **Statistics**: Total signals, sent, pending, failed, success rate
- **Channel Overview**: List monitored channels with stats
- **Signal History**: Paginated list of extracted signals
- **Real-time Updates**: Auto-refresh every 5 seconds

## Technical Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: MongoDB
- **Telegram Client**: Pyrogram
- **AI Integration**: emergentintegrations library with Emergent LLM key

### Frontend (React)
- **Framework**: React 18
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **State Management**: React hooks

### Database Collections
- `channels`: Monitored channels
- `signals`: Parsed signals with status
- `raw_messages`: Original messages
- `logs`: System logs
- `sessions`: Session data

## API Endpoints

### Session
- `GET /api/session/status` - Get session status
- `POST /api/session/send-code` - Send verification code
- `POST /api/session/verify-code` - Verify code
- `POST /api/session/verify-password` - Verify 2FA password
- `POST /api/session/connect` - Connect to existing session
- `POST /api/session/disconnect` - Disconnect

### Channels
- `GET /api/channels/available` - Get subscribeable channels
- `GET /api/channels` - Get monitored channels
- `POST /api/channels` - Add channel
- `PUT /api/channels/{id}` - Update channel
- `DELETE /api/channels/{id}` - Delete channel

### Monitoring
- `POST /api/monitoring/start` - Start monitoring
- `POST /api/monitoring/stop` - Stop monitoring
- `GET /api/monitoring/status` - Get monitoring status

### Signals
- `GET /api/signals` - Get signals (paginated)
- `GET /api/signals/{id}` - Get signal details

### Stats
- `GET /api/stats` - Get dashboard statistics
- `GET /api/health` - Health check

## Configuration

### Environment Variables
```
TELEGRAM_API_ID=<your_api_id>
TELEGRAM_API_HASH=<your_api_hash>
TELEGRAM_PHONE=<your_phone>
TELEGRAM_ADMIN_ID=<admin_telegram_id>
MONGO_URL=mongodb://localhost:27017
WEBHOOK_URL=https://zcdggtjwrtrqhqrngfau.supabase.co/functions/v1/fastsignal-webhook
WEBHOOK_API_KEY=<optional>
EMERGENT_LLM_KEY=<your_emergent_key>
```

## User Flow

1. **Setup**: Enter Telegram API credentials in .env
2. **Connect**: Click Connect → Enter phone → Verify code → (optional 2FA)
3. **Add Channels**: View available channels → Select and add to monitoring
4. **Start Monitoring**: Click "Start Monitoring" to begin extraction
5. **View Results**: Dashboard shows stats, signals page shows extracted trades

## Future Enhancements
- Signal backtesting
- Performance analytics
- Multi-symbol support
- Custom parsing rules per channel
- Discord/Slack notifications
