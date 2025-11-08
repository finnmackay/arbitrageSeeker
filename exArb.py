"""
Arbitrage Scanner Script
Scans matched markets for arbitrage opportunities between Polymarket and Kalshi
"""
from logger import setup_logger
from database import DatabaseManager
from arbitrage_detector import ArbitrageDetector
import config

# Set up logging
logger = setup_logger()


def main():
    """Main execution function for arbitrage scanning"""
    try:
        logger.info("=" * 60)
        logger.info("Starting Arbitrage Scanner")
        logger.info("=" * 60)

        # Initialize components
        logger.info("Initializing database...")
        db = DatabaseManager()

        logger.info("Initializing arbitrage detector...")
        detector = ArbitrageDetector()

        # Retrieve matched markets
        logger.info("Loading matched markets from database...")
        matched_markets = db.get_all_matches()

        if not matched_markets:
            logger.warning("No matched markets found in database.")
            logger.info("Please run main.py first to fetch and match markets.")
            return

        logger.info(f"Loaded {len(matched_markets)} matched markets")

        # Scan for arbitrage opportunities
        logger.info("Scanning for arbitrage opportunities...")
        opportunities = detector.scan_all_matches(matched_markets)

        # Display results
        logger.info("=" * 60)
        logger.info("Arbitrage Scan Results")
        logger.info("=" * 60)

        if opportunities:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities!")

            for i, opp in enumerate(opportunities, 1):
                logger.info("")
                logger.info(f"Opportunity #{i}:")
                logger.info(f"  Type: {opp['type']}")
                logger.info(f"  Polymarket: {opp['polymarket_question'][:80]}...")
                logger.info(f"  Kalshi: {opp['kalshi_title'][:80]}...")
                logger.info(f"  Action: {opp['action']}")
                logger.info(f"  Net Profit Margin: {opp['net_profit_margin']:.2%}")
                logger.info(f"  Gross Profit Margin: {opp['gross_profit_margin']:.2%}")
                logger.info(f"  Total Cost: ${opp['total_cost']:.4f}")

                if opp['type'] == 'Yes-No':
                    logger.info(f"  Polymarket YES: ${opp['polymarket_yes_price']:.4f}")
                    logger.info(f"  Kalshi NO: ${opp['kalshi_no_price']:.4f}")
                else:
                    logger.info(f"  Polymarket NO: ${opp['polymarket_no_price']:.4f}")
                    logger.info(f"  Kalshi YES: ${opp['kalshi_yes_price']:.4f}")

        else:
            logger.info("No arbitrage opportunities found at this time.")
            logger.info(f"Minimum profit threshold: {config.MIN_PROFIT_MARGIN:.2%}")
            logger.info("Try again later or adjust MIN_PROFIT_MARGIN in your .env file.")

        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in arbitrage scanner: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
