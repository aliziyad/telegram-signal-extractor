# 🏃 Quick Start - Local Development

Get the system running locally in 5 minutes.

## Option 1: Using Docker (Recommended)

### Prerequisites
- Docker & Docker Compose installed
- Your `.env` file with credentials

### Run

```bash
# Clone repo
git clone YOUR_REPO_URL
cd telegram-signal-extractor

# Copy env template
cp .env.example .env

# Edit .env with your values
nano .env

# Start everything
docker-compose up -d

# Wait for database to be ready (~30 seconds)
docker logs -f signal-extractor-app

# Access dashboard
# http://localhost:5000
# Default: admin / admin
```

### View Logs
```bash
docker logs -f signal-extractor-app
```

### Stop Everything
```bash
docker-compose down
```

## Option 2: Manual Setup

### Prerequisites
- Python 3.11+
- PostgreSQL running locally
- pip

### Setup Steps

```bash
# Clone repo
git clone YOUR_REPO_URL
cd telegram-signal-extractor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Edit with your values

# Create database
createdb signal_extractor

# Initialize tables
python -c "from app.database.connection import init_db; init_db()"

# Run the app
python main.py
```

The dashboard will be available at `http://localhost:5000`

## First-Time Setup

1. **Get Telegram Credentials**
   ```
   1. Go to https://my.telegram.org/apps
   2. Create app or use existing
   3. Copy API_ID and API_HASH
   4. Note your phone number
   ```

2. **Get Supabase Keys**
   ```
   From your Supabase project:
   - Copy SUPABASE_INGEST_URL
   - Copy SUPABASE_API_KEY
   - Copy COPY_SIGNAL_API_KEY
   ```

3. **Get Claude API Key** (free tier available)
   ```
   1. Go to https://console.anthropic.com
   2. Create API key
   3. Copy to .env
   ```

4. **Update .env**
   ```
   TELEGRAM_API_ID=your_id
   TELEGRAM_API_HASH=your_hash
   TELEGRAM_PHONE=+1234567890
   SUPABASE_INGEST_URL=...
   SUPABASE_API_KEY=...
   COPY_SIGNAL_API_KEY=...
   CLAUDE_API_KEY=sk-...
   ADMIN_PASSWORD=your_password
   ```

5. **Start the app**
   ```
   # Docker
   docker-compose up -d

   # Or Manual
   python main.py
   ```

## Login to Dashboard

- URL: `http://localhost:5000`
- Username: `admin`
- Password: Whatever you set in `ADMIN_PASSWORD`

## Add Test Channel

1. Go to "Channels" tab
2. Click "+ Add Channel"
3. Enter channel ID (starts with `-100`)
4. Give it a name

To get a channel ID:
```
Option A: Use bot
- Message @username_to_id_bot in Telegram
- Forward message from your channel

Option B: URL
- Channel URL: https://t.me/channel_name
- ID: -100followed_by_number
```

## Send Test Signal

Go to your monitored channel and post:

```
GOLD SNIPERS
XAUUSD BUY

ENTRY 2487-2480
SL 4470
TP 4492
TP 4497
TP 4500
TP 4510
```

Watch it appear in dashboard "Signals" tab within seconds!

## Monitor Logs

**Docker:**
```bash
docker logs -f signal-extractor-app
```

**Manual:**
```bash
tail -f logs/signal_extractor.log
```

## Common Issues

### "Telegram client not connected"
- Make sure API_ID and API_HASH are correct
- Check TELEGRAM_PHONE format: `+` followed by country code
- Delete `sessions/` folder to force re-auth

### "Database connection error"
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- For Docker: Wait 30s for `postgres` service to start
- Manual: Run `createdb signal_extractor`

### "Import error" for Flask/Anthropic
- Ensure virtual environment is activated
- Reinstall: `pip install -r requirements.txt`

### Dashboard shows "Offline"
- Check health: `curl http://localhost:5000/api/health`
- Check logs for exceptions
- Restart: `docker-compose restart` or `Ctrl+C` then `python main.py`

## Development Workflow

### Making Changes

1. Edit files (hot reload enabled for Flask)
2. Docker rebuild: `docker-compose up -d --build`
3. Manual restart: `Ctrl+C` then `python main.py`

### Testing Parsing

Edit `test_signal` in dashboard or directly:
```python
from app.extractors.signal_parser import SignalParser

parser = SignalParser()
result, method = parser.parse_signal("XAUUSD BUY\nEntry: 2350\nSL: 2345")
print(result)
```

### Database Inspection

```bash
# Docker
docker exec -it signal-extractor-db psql -U signal_user -d signal_extractor

# Manual (if local PostgreSQL)
psql -U signal_user -d signal_extractor

# Query examples
SELECT * FROM parsed_signals ORDER BY extracted_at DESC LIMIT 10;
SELECT * FROM telegram_channels;
SELECT COUNT(*) FROM parsed_signals;
```

## Performance Tips

### For Testing Multiple Channels
1. Keep number small (5-10) for testing
2. Monitor CPU/Memory in Docker: `docker stats`
3. Check database size: `SELECT pg_size_pretty(pg_database_size('signal_extractor'));`

### For Development
1. Set `LOG_LEVEL=DEBUG` for detailed logs
2. Use `FLASK_DEBUG=true` for auto-reload
3. Keep `REGEX_ENABLED=true` (fast, no API calls)

### Before Going Live
1. Test with `CLAUDE_ENABLED=true`
2. Verify all 3 take profits are captured
3. Check Supabase integration works
4. Review 100+ signals for accuracy

## Next Steps

1. ✅ System running locally
2. 📡 Add your Telegram channels
3. 🧪 Send test signals
4. 📊 Monitor dashboard
5. 🌐 Deploy to DigitalOcean (see DEPLOYMENT.md)

---

**Need help?**
- Check README.md for full documentation
- Review DEPLOYMENT.md for production setup
- Check GitHub Issues for common problems
