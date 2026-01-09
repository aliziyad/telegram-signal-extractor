# 🚀 DigitalOcean Apps Deployment Guide

This guide walks you through deploying the Telegram Signal Extractor on DigitalOcean Apps with one click.

## Prerequisites

- GitHub account with this repository forked/pushed
- DigitalOcean account (free credits available)
- Telegram API credentials
- (Optional) AI API keys for signal parsing

## Step 1: Get Telegram Credentials

1. Go to https://my.telegram.org/apps
2. Login with your Telegram account
3. Create a new application or use existing one
4. Copy:
   - **API ID** → `TELEGRAM_API_ID`
   - **API Hash** → `TELEGRAM_API_HASH`
5. Note your phone number → `TELEGRAM_PHONE`

## Step 2: Prepare Environment Variables

Create a document with all required variables (we'll paste in DO):

```
# Required
TELEGRAM_API_ID=YOUR_VALUE
TELEGRAM_API_HASH=YOUR_VALUE
TELEGRAM_PHONE=YOUR_VALUE

# Supabase (already have from your setup)
SUPABASE_INGEST_URL=https://zcdggtjwrtrqhqrngfau.supabase.co/functions/v1/ingest-copy-signal
SUPABASE_API_KEY=YOUR_VALUE
COPY_SIGNAL_API_KEY=YOUR_VALUE

# AI APIs (at least Claude recommended)
CLAUDE_API_KEY=sk-... (get from https://console.anthropic.com)
GEMINI_API_KEY=optional
OPENAI_API_KEY=optional

# Admin Access
ADMIN_USERNAME=admin
ADMIN_PASSWORD=STRONG_PASSWORD_HERE
SECRET_KEY=GENERATE_RANDOM_STRING_HERE

# Optional
LOG_LEVEL=INFO
```

## Step 3: Create DigitalOcean App

1. **Go to DigitalOcean Dashboard**
   - https://cloud.digitalocean.com

2. **Click "Create" → "Apps"**

3. **Connect GitHub Repository**
   - Choose "GitHub" source
   - Authenticate if needed
   - Select `YOUR_USERNAME/telegram-signal-extractor`
   - Select `main` branch
   - ✅ Check "Autodeploy on push"

4. **Review App Spec**
   - The system should auto-detect `app.yaml`
   - If not, paste contents of `app.yaml` from repo

5. **Configure PostgreSQL Database**
   - Click "Add Resource"
   - Select "Database"
   - Choose "PostgreSQL 14"
   - Cluster name: `signal-extractor-db`
   - Size: `Basic` ($15/month)
   - ✅ Wait for database to be created

## Step 4: Add Environment Variables

### Via DO Dashboard

1. **Go to your App → Settings → Environment Variables**

2. **Add each variable from your prepared list:**
   - Click "Edit" next to component
   - Add each `KEY=VALUE` pair
   - ✅ Make sure database URL is auto-populated

3. **Database URL Format**
   ```
   postgresql://[user]:[password]@[host]:[port]/[database]
   ```
   - DO provides this automatically
   - It starts with `postgresql://`

4. **Save changes**

### Critical Variables

Must be set for system to work:

```
TELEGRAM_API_ID          # From my.telegram.org
TELEGRAM_API_HASH        # From my.telegram.org
TELEGRAM_PHONE           # Your phone number
SUPABASE_INGEST_URL      # Your Supabase endpoint
COPY_SIGNAL_API_KEY      # Your API key
CLAUDE_API_KEY           # For signal parsing
ADMIN_PASSWORD           # Strong password!
SECRET_KEY               # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 5: Review & Deploy

1. **Review Final Configuration**
   - ✅ App name: `telegram-signal-extractor`
   - ✅ Database: PostgreSQL 14
   - ✅ All env vars populated
   - ✅ Instance size: Basic

2. **Click "Create Resources"**
   - This will:
     - Create PostgreSQL database
     - Build Docker image
     - Deploy the app
     - Initialize database tables
   - Takes ~5-10 minutes

3. **Monitor Deployment**
   - Watch the "Deployments" tab
   - Check logs for any errors
   - Wait for "ACTIVE" status

## Step 6: Access Your Application

1. **Get App URL**
   - Go to your App dashboard
   - Copy the app URL (something like `https://signal-extractor-xxx.ondigitalocean.app`)

2. **Login to Dashboard**
   - Visit: `https://your-app-url/`
   - Username: `admin`
   - Password: The one you set in env vars

3. **Add Telegram Channels**
   - Go to "Channels" tab
   - Click "+ Add Channel"
   - Get channel IDs from Telegram:
     ```python
     # In Telegram, type this in any chat:
     @username_to_id_bot
     # Or forward message from channel
     ```
   - Add channels you want to monitor

## Step 7: Verify Everything Works

1. **Check Dashboard Stats**
   - Should show 0 signals (waiting for messages)
   - Status indicator should be green "Online"

2. **Monitor Logs**
   - Go to "Logs" tab
   - Should see initialization messages

3. **Send Test Signal**
   - Go to one of your monitored channels
   - Post a test signal:
     ```
     XAUUSD BUY
     Entry: 2350.50
     SL: 2345.00
     TP1: 2360.00
     ```

4. **Watch It Parse**
   - Return to dashboard "Signals" tab
   - Should see your test signal within seconds
   - Check "Parsing Method" (should be "regex" if using sample format)

## Step 8: Scale & Optimize

### Increase Instance Size
If handling heavy load:
1. Go to Settings → Components
2. Increase instance size (currently `basic-xs`)
3. Options: `basic-xs`, `basic-s`, `basic-m`, `basic-l`

### Monitor Costs
- PostgreSQL: $15/month base
- App: Varies by instance size
  - `basic-xs`: $5/month
  - `basic-s`: $10/month
  - `basic-m`: $20/month

### Enable More Channels
- System supports 100+ channels
- Just add them in dashboard
- Performance scales linearly

## Troubleshooting

### App Won't Deploy
**Check:**
- All required env vars are set
- Database is created and running
- GitHub token is valid

**Solution:**
- Delete app, recreate with better env vars
- Check "Deployments" tab for error logs

### Dashboard Not Loading
**Check:**
- App is showing "ACTIVE" status
- Database is running
- Browser cache (try incognito)

**Solution:**
```bash
# Restart the app from dashboard
# Or force clear cache: Ctrl+Shift+Delete
```

### No Signals Appearing
**Check:**
- Channels are added and active
- Phone can receive Telegram messages
- Channel IDs are correct

**Solution:**
- Go to "Logs" tab, check for errors
- Verify channel ID format (should start with `-100`)
- Try sending test message to channel

### Parsing All Signals Fails
**Check:**
- Claude API key is valid
- Account has credit/usage remaining
- Regex enabled (fallback)

**Solution:**
- Add GEMINI_API_KEY or OPENAI_API_KEY as backup
- Check "Errors" tab for specific parsing issues
- Improve regex patterns for specific channels

### Database Connection Error
**Check:**
- Database URL is correct
- Database is running (green status)
- No special characters in password (URL encode if needed)

**Solution:**
- Reset database connection string
- Recreate database if corrupted
- Check DO status page for incidents

## Auto-Deployment

Every push to `main` branch automatically:
1. Runs tests
2. Builds new Docker image
3. Deploys new version
4. Zero downtime update

To deploy changes:
```bash
git add .
git commit -m "Update signal parsing rules"
git push origin main
```

Watch deployment in "Deployments" tab.

## Monitoring & Maintenance

### Regular Checks

**Daily:**
- Dashboard shows signals being captured
- No errors in "Errors" tab
- Success rate > 90%

**Weekly:**
- Review logs for any warnings
- Check parsing method distribution
- Monitor database size

**Monthly:**
- Analyze signal accuracy
- Optimize regex patterns
- Update AI API keys if needed

### Logs

Access logs:
1. Dashboard → Logs tab (last 100)
2. Or CLI: `doctl apps logs get-logs APP_ID`

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check README.md
- **Logs**: Always check app logs first
- **Discord/Forums**: Ask community

## Next Steps

1. ✅ System is now running and monitoring channels
2. 📊 Monitor dashboard daily
3. 🎯 Test with real trading signals
4. 🔧 Optimize regex patterns per channel
5. 📈 Scale as needed

---

**Congratulations! Your Telegram Signal Extractor is now live!** 🎉

Your dashboard is live at: `https://YOUR_APP_URL/`

Admin panel access to manage channels, monitor signals, and view parsing errors.
