"""
API Client Management
Centralized API client initialization and management
"""
import logging
from kalshi_client.client import KalshiClient
from cryptography.hazmat.primitives import serialization
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
import config

logger = logging.getLogger(__name__)


class APIClientManager:
    """Manages API client initialization and provides singleton access"""

    _kalshi_client = None
    _polymarket_client = None

    @classmethod
    def get_kalshi_client(cls):
        """Get or create Kalshi client instance"""
        if cls._kalshi_client is None:
            try:
                if config.MOCK_MODE:
                    logger.warning("Running in MOCK_MODE - Kalshi client not initialized")
                    return None

                if not config.KALSHI_KEY_ID or not config.KALSHI_PRIVATE_KEY:
                    raise ValueError("Kalshi credentials not configured. Check your .env file.")

                private_key = serialization.load_pem_private_key(
                    config.KALSHI_PRIVATE_KEY.encode(),
                    password=None
                )
                cls._kalshi_client = KalshiClient(
                    key_id=config.KALSHI_KEY_ID,
                    private_key=private_key
                )
                logger.info("Kalshi client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Kalshi client: {e}")
                raise

        return cls._kalshi_client

    @classmethod
    def get_polymarket_client(cls):
        """Get or create Polymarket client instance"""
        if cls._polymarket_client is None:
            try:
                if config.MOCK_MODE:
                    logger.warning("Running in MOCK_MODE - Polymarket client not initialized")
                    return None

                if not config.POLY_PRIVATE_KEY:
                    raise ValueError("Polymarket credentials not configured. Check your .env file.")

                cls._polymarket_client = ClobClient(
                    host="https://clob.polymarket.com",
                    key=config.POLY_PRIVATE_KEY,
                    chain_id=POLYGON
                )
                logger.info("Polymarket client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Polymarket client: {e}")
                raise

        return cls._polymarket_client

    @classmethod
    def reset_clients(cls):
        """Reset client instances (useful for testing or credential rotation)"""
        cls._kalshi_client = None
        cls._polymarket_client = None
        logger.info("API clients reset")


def fetch_polymarket_markets(client=None):
    """
    Fetch all Polymarket markets with pagination

    Args:
        client: Optional ClobClient instance. If None, uses singleton.

    Returns:
        list: All available markets
    """
    if client is None:
        client = APIClientManager.get_polymarket_client()

    if client is None:
        logger.warning("Polymarket client not available, returning empty list")
        return []

    all_markets = []
    next_cursor = ""

    try:
        while True:
            response = client.get_markets(next_cursor=next_cursor)
            if "data" in response:
                all_markets.extend(response["data"])

            next_cursor = response.get("next_cursor")
            if next_cursor == "LTE=" or not next_cursor:
                break

        logger.info(f"Fetched {len(all_markets)} markets from Polymarket")
        return all_markets
    except Exception as e:
        logger.error(f"Error fetching Polymarket markets: {e}")
        raise


def fetch_kalshi_markets(client=None):
    """
    Fetch all Kalshi markets with pagination

    Args:
        client: Optional KalshiClient instance. If None, uses singleton.

    Returns:
        list: All available markets
    """
    if client is None:
        client = APIClientManager.get_kalshi_client()

    if client is None:
        logger.warning("Kalshi client not available, returning empty list")
        return []

    all_markets = []
    cursor = None
    limit = 100

    try:
        while True:
            response = client.get_markets(cursor=cursor, limit=limit, status="open")
            if "markets" in response:
                all_markets.extend(response["markets"])

            cursor = response.get("cursor")
            if not cursor:
                break

        logger.info(f"Fetched {len(all_markets)} markets from Kalshi")
        return all_markets
    except Exception as e:
        logger.error(f"Error fetching Kalshi markets: {e}")
        raise


def get_polymarket_price(market_id, client=None):
    """
    Get current prices for a Polymarket market

    Args:
        market_id: Polymarket condition ID
        client: Optional ClobClient instance

    Returns:
        dict: {"yes_price": float, "no_price": float} or None on error
    """
    if client is None:
        client = APIClientManager.get_polymarket_client()

    if client is None:
        return None

    try:
        response = client.get_market(market_id)
        yes_price = float(response["tokens"][0]["price"])
        no_price = float(response["tokens"][1]["price"])

        return {
            "yes_price": yes_price,
            "no_price": no_price,
            "question": response.get("question", "")
        }
    except Exception as e:
        logger.error(f"Error fetching Polymarket price for {market_id}: {e}")
        return None


def get_kalshi_price(ticker, client=None):
    """
    Get current prices for a Kalshi market

    Args:
        ticker: Kalshi market ticker
        client: Optional KalshiClient instance

    Returns:
        dict: {"yes_price": float, "no_price": float} or None on error
    """
    if client is None:
        client = APIClientManager.get_kalshi_client()

    if client is None:
        return None

    try:
        response = client.get_market(ticker)
        kalshi_market = response.get("market", {})

        yes_bid = kalshi_market.get("yes_ask")
        no_bid = kalshi_market.get("no_ask")

        if yes_bid is None or no_bid is None:
            logger.warning(f"Missing price data for Kalshi ticker {ticker}")
            return None

        yes_price = float(yes_bid) / 100
        no_price = float(no_bid) / 100

        return {
            "yes_price": yes_price,
            "no_price": no_price,
            "title": kalshi_market.get("title", "")
        }
    except Exception as e:
        logger.error(f"Error fetching Kalshi price for {ticker}: {e}")
        return None
