# Telegram Signal Extractor - Product Requirements Document

## Overview
A comprehensive system that connects to a user's Telegram account, monitors selected channels for trading signals, parses them using AI (Gemini → Claude → OpenAI fallback), and sends extracted signals to an external webhook endpoint.

## Recent Updates (January 12, 2026)
- ✅ Implemented JWT-based admin authentication (credentials: aliziyad / tM23v8Mr!@#)
- ✅ Added dark/light theme toggle with localStorage persistence
- ✅ Implemented collapsible sidebar navigation
- ✅ Hidden "Made with Emergent" badge via CSS and JS
- ✅ Backend auth endpoints: POST /api/auth/login, POST /api/auth/verify
- ✅ All tests passing (13/13 backend tests)

## Core Features

### 1. Admin Authentication (NEW)
- **JWT-based login**: Secure authentication with 24-hour token expiry
- **Credentials**: Username and password stored in environment variables
- **Session persistence**: Login state saved in localStorage
- **Auto logout**: Sessions expire after 24 hours

### 2. Telegram Session Management
- **Connect/Disconnect**: Secure authentication flow with phone number verification
- **2FA Support**: Handle two-factor authentication if enabled
- **Session Persistence**: Maintain session across restarts using pyrogram sessions
- **Disconnection Alerts**: Send Telegram notifications to admin when session disconnects

### 3. Channel Management
- **Auto-Discovery**: Extract all channels, supergroups, and groups the user is subscribed to
- **Selective Monitoring**: Add/remove channels from monitoring list
- **Channel Stats**: Track signals extracted per channel

### 4. Signal Extraction
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

### 5. Signal Modifications
- **Edit Detection**: Detect when original signal messages are edited
- **Reply Parsing**: Parse reply messages for modifications:
  - Move SL (Stop Loss updates)
  - Cancel trade
  - Close trade
  - Partial close
  - General updates

### 6. Webhook Integration
- **External Webhook**: Send signals to external endpoint
- **Webhook URL**: https://zcdggtjwrtrqhqrngfau.supabase.co/functions/v1/fastsignal-webhook
- **Payload Format**: JSON with channel_id, parsed_data, timestamps

### 7. Dashboard & UI
- **Statistics**: Total signals, sent, pending, failed, success rate
- **Channel Overview**: List monitored channels with stats
- **Signal History**: Paginated list of extracted signals with filters
- **Real-time Updates**: Auto-refresh every 5 seconds
- **Dark/Light Theme**: Toggle with localStorage persistence
- **Collapsible Sidebar**: Icon-only mode for more space

## Technical Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: MongoDB
- **Telegram Client**: Pyrogram
- **AI Integration**: emergentintegrations library with Emergent LLM key
- **Authentication**: PyJWT for token generation/verification

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

### Authentication (NEW)
- `POST /api/auth/login` - Login with username/password, returns JWT token
- `POST /api/auth/verify` - Verify JWT token validity

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
- `GET /api/signals` - Get signals (paginated, with filters)
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
ADMIN_USERNAME=aliziyad
ADMIN_PASSWORD=tM23v8Mr!@#
SECRET_KEY=<jwt_secret>
```

## User Flow

1. **Login**: Enter admin credentials to access dashboard
2. **Setup**: Enter Telegram API credentials in .env
3. **Connect**: Click Connect → Enter phone → Verify code → (optional 2FA)
4. **Add Channels**: View available channels → Select and add to monitoring
5. **Start Monitoring**: Click "Start Monitoring" to begin extraction
6. **View Results**: Dashboard shows stats, signals page shows extracted trades
7. **Customize UI**: Toggle dark/light theme, collapse sidebar as needed

## Pending Tasks (P2)
- Implement signal modification logic (move SL, close trade updates)
- Verify persistent monitoring (service runs after admin logout)

## Future Enhancements
- Signal backtesting
- Performance analytics
- Multi-symbol support
- Custom parsing rules per channel
- Discord/Slack notifications
