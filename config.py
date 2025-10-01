"""
Configuration management for arbitrage bot
DO NOT COMMIT .env FILE TO GIT
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
KALSHI_KEY_ID = os.getenv("KALSHI_KEY_ID", "")
KALSHI_PRIVATE_KEY = os.getenv("KALSHI_PRIVATE_KEY", "")
POLY_PRIVATE_KEY = os.getenv("POLY_PRIVATE_KEY", "")

# Blockchain Configuration
POLYGON_RPC = "https://polygon-rpc.com"
USDC_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# Monitoring Configuration
SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "5"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))
MIN_PROFIT_MARGIN = float(os.getenv("MIN_PROFIT_MARGIN", "0.02"))  # 2% minimum profit

# Alert Configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ALERT_METHOD = os.getenv("ALERT_METHOD", "console")  # console, discord, telegram

# Fee Configuration (for profit calculations)
KALSHI_FEE_PERCENT = float(os.getenv("KALSHI_FEE_PERCENT", "0.007"))  # 0.7%
POLYMARKET_GAS_FEE_USD = float(os.getenv("POLYMARKET_GAS_FEE_USD", "0.10"))  # ~$0.10 gas

# Risk Management
MAX_POSITION_USD = float(os.getenv("MAX_POSITION_USD", "1000"))
ENABLE_AUTO_TRADE = os.getenv("ENABLE_AUTO_TRADE", "false").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "arbitrage_bot.log")

# Database
DB_PATH = os.getenv("DB_PATH", "markets.db")

# Mock Mode (for testing without API keys)
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
