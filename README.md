# Arbitrage Seeker Bot

An automated arbitrage detection bot that identifies profitable trading opportunities between **Polymarket** and **Kalshi** prediction markets using semantic market matching and real-time price monitoring.

## Features

- **Intelligent Market Matching**: Uses ML-based semantic similarity (SentenceTransformers) to match equivalent markets across platforms
- **Real-Time Arbitrage Detection**: Monitors matched markets for profitable Yes-No and No-Yes arbitrage opportunities
- **Multi-Channel Notifications**: Send alerts via Console, Discord, or Telegram
- **Modular Architecture**: Clean, maintainable codebase with proper separation of concerns
- **Comprehensive Logging**: Track all operations with configurable logging levels
- **Secure Configuration**: Environment-based configuration with no hardcoded credentials
- **Continuous Monitoring**: Run one-time scans or continuous monitoring mode

## Architecture

```
arbitrageSeeker/
├── config.py              # Configuration management
├── logger.py              # Logging setup
├── api_clients.py         # API client management (Polymarket, Kalshi)
├── database.py            # Database operations layer
├── market_matcher.py      # Semantic market matching
├── arbitrage_detector.py  # Arbitrage opportunity detection
├── notifications.py       # Multi-channel alerts
├── main.py                # Market matching script
├── exArb.py               # Arbitrage scanning script
├── run.py                 # Main orchestration script
└── markets.db             # SQLite database
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd arbitrageSeeker

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
# API Credentials
KALSHI_KEY_ID=your_kalshi_key_id
KALSHI_PRIVATE_KEY=your_kalshi_private_key
POLY_PRIVATE_KEY=your_polygon_private_key

# Monitoring Settings
SCAN_INTERVAL_MINUTES=5
SIMILARITY_THRESHOLD=0.85
MIN_PROFIT_MARGIN=0.02

# Notification Settings
ALERT_METHOD=console  # Options: console, discord, telegram
DISCORD_WEBHOOK_URL=  # Optional
TELEGRAM_BOT_TOKEN=   # Optional
TELEGRAM_CHAT_ID=     # Optional

# Mock Mode (for testing without API keys)
MOCK_MODE=false
```

### 3. Usage

#### Run Full Pipeline (Recommended)

```bash
# Run once
python run.py

# Or explicitly
python run.py once
```

#### Continuous Monitoring

```bash
python run.py monitor
```

This will:
1. Match markets every N minutes (configured in SCAN_INTERVAL_MINUTES)
2. Scan for arbitrage opportunities
3. Send notifications when opportunities are found

#### Run Individual Components

```bash
# Only match markets
python run.py match

# Only scan for arbitrage
python run.py scan

# Or use the individual scripts
python main.py      # Match markets
python exArb.py     # Scan for arbitrage
```

## Requirements

- Python 3.8+
- API credentials for Polymarket and Kalshi
- Internet connection for API access

### Dependencies

All dependencies are listed in `requirements.txt`:

```
sentence-transformers>=2.0.0  # ML-based market matching
py-clob-client>=0.1.0         # Polymarket API
kalshi-python>=0.1.0          # Kalshi API
cryptography>=41.0.0          # Key management
python-dotenv>=1.0.0          # Environment variables
schedule>=1.2.0               # Task scheduling
requests>=2.31.0              # HTTP requests
pandas>=2.0.0                 # Data manipulation
tabulate>=0.9.0               # Table formatting
```

## How It Works

### 1. Market Matching (main.py)

The bot fetches all available markets from both Polymarket and Kalshi, then uses a SentenceTransformer model (all-mpnet-base-v2) to compute semantic similarity between market questions:

1. Fetch markets from both platforms with pagination
2. Encode market questions/titles into embeddings
3. Compute cosine similarity between all pairs
4. Store matches above threshold (default 85%) in database

### 2. Arbitrage Detection (exArb.py)

For each matched market pair, the bot:

1. Fetches current YES/NO prices from both platforms
2. Checks two arbitrage conditions:
   - **Yes-No**: Buy YES on Polymarket, NO on Kalshi
   - **No-Yes**: Buy NO on Polymarket, YES on Kalshi
3. Calculates gross and net profit (accounting for fees)
4. Reports opportunities above minimum profit threshold

### 3. Notifications

When an opportunity is found, the bot sends an alert containing:

- Market details from both platforms
- Opportunity type (Yes-No or No-Yes)
- Current prices
- Gross and net profit margins
- Recommended action

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KALSHI_KEY_ID` | Kalshi API key ID | Required |
| `KALSHI_PRIVATE_KEY` | Kalshi private key | Required |
| `POLY_PRIVATE_KEY` | Polygon private key for Polymarket | Required |
| `SCAN_INTERVAL_MINUTES` | Minutes between scans in monitor mode | 5 |
| `SIMILARITY_THRESHOLD` | Minimum similarity for market matching (0-1) | 0.85 |
| `MIN_PROFIT_MARGIN` | Minimum profit to report (0-1) | 0.02 (2%) |
| `ALERT_METHOD` | Notification method: console, discord, telegram | console |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | Optional |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Optional |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | Optional |
| `KALSHI_FEE_PERCENT` | Kalshi trading fee | 0.007 (0.7%) |
| `POLYMARKET_GAS_FEE_USD` | Polymarket gas fee estimate | 0.10 |
| `MAX_POSITION_USD` | Maximum position size | 1000 |
| `ENABLE_AUTO_TRADE` | Enable automatic trading | false |
| `LOG_LEVEL` | Logging level: DEBUG, INFO, WARNING, ERROR | INFO |
| `LOG_FILE` | Log file path | arbitrage_bot.log |
| `DB_PATH` | Database file path | markets.db |
| `MOCK_MODE` | Run without API credentials | true |

## Security Best Practices

1. **Never commit your `.env` file** - It's in `.gitignore` for a reason
2. **Keep API keys secure** - Use environment variables, not hardcoded values
3. **Rotate credentials regularly** - Update keys periodically
4. **Review permissions** - Ensure API keys have minimum required permissions
5. **Monitor usage** - Watch for unusual API activity

## Troubleshooting

### "No Polymarket/Kalshi markets fetched"

- Check your API credentials in `.env`
- Verify internet connection
- Check if APIs are experiencing downtime
- Set `MOCK_MODE=true` to test without real credentials

### "No matches found"

- Lower `SIMILARITY_THRESHOLD` in `.env` (e.g., 0.75)
- Verify both platforms have active markets
- Check database: `sqlite3 markets.db "SELECT COUNT(*) FROM matched_markets;"`

### "No arbitrage opportunities found"

- Lower `MIN_PROFIT_MARGIN` in `.env`
- Market efficiency may eliminate arbitrage quickly
- Try running during high-volatility events
- Ensure real-time price data is accessible

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## Development

### Project Structure

- `config.py` - Centralized configuration with environment variable loading
- `logger.py` - Logging setup with file and console handlers
- `api_clients.py` - API client management with singleton pattern
- `database.py` - Database layer with context managers
- `market_matcher.py` - Semantic similarity matching with SentenceTransformers
- `arbitrage_detector.py` - Arbitrage detection logic with fee calculations
- `notifications.py` - Multi-channel notification system
- `run.py` - Main orchestrator with scheduling

### Adding Features

The modular architecture makes it easy to extend:

1. **New notification channel**: Add method to `notifications.py`
2. **New exchange**: Extend `api_clients.py`
3. **Advanced matching**: Modify `market_matcher.py`
4. **Custom strategies**: Extend `arbitrage_detector.py`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Disclaimer

This bot is for educational and research purposes only. Cryptocurrency and prediction market trading carries risk. Always:

- Understand the risks before trading
- Start with small positions
- Verify opportunities manually
- Comply with platform terms of service
- Follow local regulations

The authors are not responsible for any financial losses.

## License

[Specify your license here]

## Support

For issues, questions, or contributions, please open an issue on GitHub.
