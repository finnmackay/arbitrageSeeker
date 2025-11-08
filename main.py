"""
Market Matcher Script
Fetches markets from Polymarket and Kalshi, finds semantic matches, and stores them in database
"""
from logger import setup_logger
from api_clients import fetch_polymarket_markets, fetch_kalshi_markets
from market_matcher import MarketMatcher
from database import DatabaseManager
import config

# Set up logging
logger = setup_logger()


def main():
    """Main execution function for market matching"""
    try:
        logger.info("=" * 60)
        logger.info("Starting Market Matching Process")
        logger.info("=" * 60)

        # Initialize components
        logger.info("Initializing database...")
        db = DatabaseManager()

        logger.info("Initializing market matcher...")
        matcher = MarketMatcher()

        # Fetch markets from both platforms
        logger.info("Fetching Polymarket markets...")
        poly_markets = fetch_polymarket_markets()

        logger.info("Fetching Kalshi markets...")
        kalshi_markets = fetch_kalshi_markets()

        if not poly_markets:
            logger.error("No Polymarket markets fetched. Exiting.")
            return

        if not kalshi_markets:
            logger.error("No Kalshi markets fetched. Exiting.")
            return

        # Find matches using semantic similarity
        logger.info(
            f"Finding matches between {len(poly_markets)} Polymarket "
            f"and {len(kalshi_markets)} Kalshi markets..."
        )

        matches = matcher.find_matches(
            poly_markets,
            kalshi_markets,
            similarity_threshold=config.SIMILARITY_THRESHOLD
        )

        if not matches:
            logger.warning("No matches found.")
            return

        # Store matches in database
        logger.info(f"Storing {len(matches)} matches in database...")
        stored_count = db.store_matches(matches)

        logger.info("=" * 60)
        logger.info(f"Market Matching Complete!")
        logger.info(f"Total matches found: {len(matches)}")
        logger.info(f"New matches stored: {stored_count}")
        logger.info(f"Total matches in database: {db.get_match_count()}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in market matching: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()




