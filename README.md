# 📡 Telegram Signal Extractor System

A production-ready, scalable system for extracting trading signals from Telegram channels in real-time, parsing them with AI/regex, and sending them to your Supabase backend.

## Features

- 🚀 **Real-time Extraction**: Monitor 100+ Telegram channels simultaneously
- 🤖 **Smart Parsing**: Regex-first, with AI fallback (Claude, Gemini, ChatGPT)
- 📊 **Web Dashboard**: Live monitoring with channel management, signal tracking, and error logs
- 🔄 **Scheduled Operation**: Runs only during extraction windows (Sun 4am - Fri 10pm Maldives time)
- 🌐 **API Integration**: Posts parsed signals to Supabase with automatic retries
- 📱 **Multi-Channel**: Handle XAUUSD and other forex pairs with configurable parsing
- 🐳 **Docker Ready**: One-click deployment on DigitalOcean Apps
- 🔐 **Secure**: Environment variables, API authentication, admin dashboard protection

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Telegram Channels (100+)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                ┌──────────▼──────────┐
                │  Pyrogram Client    │ Real-time monitoring
                │  (Async)            │ Multi-channel support
                └──────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
  ┌─────▼──────┐   ┌──────▼──────┐  ┌──────▼──────┐
  │Raw Signal  │   │  Parser     │  │  Signal     │
  │ Storage    │   │ (Regex/AI)  │  │  Sender     │
  │(PostgreSQL)│   └──────┬──────┘  │  (Async)    │
  └────────────┘          │         └──────┬──────┘
                          │                │
                   ┌──────▼──────┐   ┌─────▼─────┐
                   │ParsedSignal │   │ Supabase  │
                   │(PostgreSQL) │   │   API     │
                   └─────────────┘   └───────────┘
                          │
                   ┌──────▼──────────┐
                   │ Web Dashboard   │
                   │ (Flask/Gunicorn)│
                   └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Telegram account and API credentials
- (Optional) Claude, Gemini, ChatGPT API keys
- Git account

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/telegram-signal-extractor.git
cd telegram-signal-extractor
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Initialize database**
```bash
python -c "from app.database.connection import init_db; init_db()"
```

6. **Run the application**
```bash
python main.py
```

Access the dashboard at: `http://localhost:5000`

Default credentials:
- Username: `admin`
- Password: `admin`

## Environment Configuration

All configuration is done through environment variables (`.env` file or DO Apps secrets).

### Telegram Setup

```env
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
```

Get these from: https://my.telegram.org/apps

### Database

```env
DATABASE_URL=postgresql://user:password@host:5432/signal_extractor
```

### Supabase Integration

```env
SUPABASE_INGEST_URL=https://your-project.supabase.co/functions/v1/ingest-copy-signal
SUPABASE_API_KEY=your_api_key
COPY_SIGNAL_API_KEY=your_copy_signal_key
```

### AI APIs (Parsing Fallback)

```env
# At least one required
CLAUDE_API_KEY=sk-...
GEMINI_API_KEY=your_key
OPENAI_API_KEY=sk-...

# Enable/disable each
REGEX_ENABLED=true
CLAUDE_ENABLED=true
GEMINI_ENABLED=false
OPENAI_ENABLED=false
```

### Schedule (Maldives Time: UTC+4)

```env
SCHEDULE_START=04:00      # Sunday 4 AM
SCHEDULE_END=22:00        # Friday 10 PM
TIMEZONE=Asia/Male
```

### Security

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=strong_password
SECRET_KEY=your_secret_key_change_in_production
```

## API Integration

### Supabase Endpoint Format

The system sends signals to your Supabase edge function in this format:

```json
{
  "api_key": "YOUR_COPY_SIGNAL_API_KEY",
  "channel_id": "-1001234567890",
  "raw_message": "XAUUSD BUY\nEntry: 2350.50\nSL: 2345.00\nTP1: 2360.00",
  "timestamp": "2025-01-09T12:00:00Z",
  "parsed_data": {
    "symbol": "XAUUSD",
    "direction": "BUY",
    "entry_price": 2350.50,
    "stop_loss": 2345.00,
    "take_profit_1": 2360.00,
    "take_profit_2": 2370.00,
    "take_profit_3": null,
    "risk_percentage": 0.214,
    "parsing_method": "regex",
    "confidence_score": 1.0
  }
}
```

### Dashboard API Endpoints

- `GET /api/stats` - Overall statistics
- `GET /api/channels` - List all channels
- `POST /api/channels` - Add new channel
- `PUT /api/channels/<id>` - Update channel
- `DELETE /api/channels/<id>` - Delete channel
- `GET /api/signals` - List signals (paginated)
- `GET /api/logs` - System logs
- `GET /api/errors` - Parsing errors
- `GET /api/health` - Health check

## Signal Parsing

### Regex Patterns Supported

The system automatically extracts from messages containing:

```
SYMBOL: XAUUSD, EURUSD, GBPUSD, AUDUSD, USDJPY, GOLD, FOREX
DIRECTION: BUY, SELL, LONG, SHORT, BULLISH, BEARISH
ENTRY: ENTRY, ENTER, BUY @, @ symbol
STOP LOSS: SL, STOPLOSS, STOP LOSS
TAKE PROFIT: TP, TP1, TP2, TP3, TARGET, TARGET 1-3
```

### Example Signals

```
XAUUSD BUY
ENTRY 2350.50
SL 2345.00
TP1 2360.00
TP2 2370.00
TP3 2380.00
```

### Parsing Fallback

If regex fails:
1. Try Claude 3.5 Sonnet
2. Try Google Gemini
3. Try OpenAI GPT-3.5-turbo
4. Log error for manual review

Each AI model is prompted to return structured JSON that's parsed and validated.

## Docker Deployment

### Build Locally

```bash
docker build -t signal-extractor:latest .
```

### Run with Docker Compose

```bash
docker-compose up -d
```

See `docker-compose.yml` for configuration.

## DigitalOcean Apps Deployment

### Step-by-Step

1. **Push to GitHub**
```bash
git remote add origin https://github.com/YOUR_USERNAME/telegram-signal-extractor.git
git branch -M main
git push -u origin main
```

2. **Create DO App**
   - Go to DigitalOcean Dashboard
   - Click "Create" > "Apps"
   - Connect your GitHub repository
   - Use the `app.yaml` configuration

3. **Set Environment Variables**
   In DO App settings, add all variables from `.env.example`:
   - TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
   - DATABASE_URL (use DO's managed PostgreSQL)
   - SUPABASE_* keys
   - AI API keys
   - ADMIN_USERNAME, ADMIN_PASSWORD
   - SECRET_KEY (generate a strong one)

4. **Deploy**
   - Click "Deploy"
   - Wait for build and deployment to complete
   - Dashboard will be available at your app URL

### Auto-Deployment on Push

Every time you push to `main` branch, DO Apps automatically:
1. Pulls latest code
2. Runs tests
3. Builds Docker image
4. Deploys new version
5. Restarts services

This is configured in `.github/workflows/deploy.yml`

## Database Schema

### Tables

**telegram_channels**
- Channel ID, name, username
- Active status
- Created/updated timestamps

**raw_signals**
- Original message content
- Channel reference
- Message timestamp
- Extraction timestamp

**parsed_signals**
- Symbol, direction, entry price
- Stop loss, take profits (1-3)
- Parsing method & confidence score
- Send status and Supabase response

**extraction_logs**
- Info/warning/error messages
- Channel reference
- Metadata for debugging

**parsing_errors**
- Failed parsing attempts
- Error messages and details
- Resolution tracking

**signal_stats**
- Daily statistics per channel
- Buy/sell counts
- Success/failure rates

## Monitoring & Logs

### Access Logs

```bash
# Docker
docker logs -f signal-extractor

# Local
tail -f logs/signal_extractor.log
```

### Log Levels

Set via `LOG_LEVEL` environment variable:
- `DEBUG` - Detailed debug info
- `INFO` - General information (recommended)
- `WARNING` - Warning messages
- `ERROR` - Error messages only

### Health Check

```bash
curl http://localhost:5000/api/health
```

Returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-09T12:00:00Z"
}
```

## Troubleshooting

### Telegram Client Not Connecting

```
Error: failed to get inputAppConfig
```

Solution:
- Verify API ID and API Hash from https://my.telegram.org
- Check phone number format
- Delete `sessions/` folder and restart (will need to re-authenticate)

### Database Connection Error

```
Could not connect to server: Connection refused
```

Solution:
- Verify DATABASE_URL is correct
- Check PostgreSQL is running
- Ensure credentials are correct
- Run migrations: `python -c "from app.database.connection import init_db; init_db()"`

### Parsing Failures

Check the **Errors** tab in dashboard for specific parsing errors.

Common causes:
- Unusual message format
- Missing entry price or direction
- Wrong currency pair format

Solution:
- Improve regex patterns for specific channels
- Add channel-specific parsing rules
- Use AI APIs as fallback (more flexible)

### Supabase Connection Fails

```
Failed to send signal to Supabase
```

Solution:
- Verify SUPABASE_INGEST_URL is correct
- Check COPY_SIGNAL_API_KEY is valid
- Verify Supabase edge function is deployed
- Check function returns 200/201 status

## Performance Optimization

### For 100+ Channels

1. **Batch Processing**
   - Adjust `BATCH_SIZE` (default: 10)
   - Signals sent in batches to reduce API calls

2. **Connection Pooling**
   - Disabled for DO Apps (`NullPool`)
   - Can be enabled for dedicated servers

3. **Async Processing**
   - Both Telegram monitoring and signal sending run async
   - Non-blocking, high concurrency

4. **Database Indexing**
   - Indexes on: channel_id, extracted_at, status
   - Fast queries even with millions of signals

## Security Considerations

- ✅ Use strong ADMIN_PASSWORD
- ✅ Keep API keys in environment variables only
- ✅ Use HTTPS in production
- ✅ Database credentials in secure secrets manager
- ✅ Regular backups of PostgreSQL
- ✅ Monitor for API rate limits
- ✅ Audit logs in admin dashboard

## Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues and feature requests, please use GitHub Issues.

## Roadmap

- [ ] Signal backtesting integration
- [ ] Risk calculation improvements
- [ ] Multi-symbol support (beyond XAUUSD)
- [ ] Performance analytics dashboard
- [ ] Signal accuracy tracking
- [ ] Webhook notifications (Discord, Slack)
- [ ] Custom parsing rules per channel
- [ ] Database archival for old signals

## Changelog

### v1.0.0 (2025-01-09)
- Initial release
- Pyrogram Telegram monitoring
- Regex + AI parsing
- Web dashboard
- Supabase integration
- DO Apps deployment ready

---

Built with ❤️ for traders who want to automate signal extraction.

**Questions?** Check the [GitHub Issues](https://github.com/YOUR_USERNAME/telegram-signal-extractor/issues)
