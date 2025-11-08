"""
Main Orchestration Script
Runs the full arbitrage bot pipeline: market matching + arbitrage detection + notifications
"""
import time
import schedule
from logger import setup_logger
from api_clients import fetch_polymarket_markets, fetch_kalshi_markets
from market_matcher import MarketMatcher
from database import DatabaseManager
from arbitrage_detector import ArbitrageDetector
from notifications import NotificationService
import config

# Set up logging
logger = setup_logger()


def run_market_matching():
    """Run market matching phase"""
    try:
        logger.info("=" * 60)
        logger.info("PHASE 1: Market Matching")
        logger.info("=" * 60)

        # Initialize components
        db = DatabaseManager()
        matcher = MarketMatcher()

        # Fetch markets
        logger.info("Fetching markets from both platforms...")
        poly_markets = fetch_polymarket_markets()
        kalshi_markets = fetch_kalshi_markets()

        if not poly_markets or not kalshi_markets:
            logger.error("Failed to fetch markets from one or both platforms")
            return False

        # Find matches
        logger.info(
            f"Finding matches between {len(poly_markets)} Polymarket "
            f"and {len(kalshi_markets)} Kalshi markets..."
        )

        matches = matcher.find_matches(
            poly_markets,
            kalshi_markets,
            similarity_threshold=config.SIMILARITY_THRESHOLD
        )

        if matches:
            stored_count = db.store_matches(matches)
            logger.info(f"Stored {stored_count} new matches")
        else:
            logger.warning("No matches found")

        logger.info(f"Total matches in database: {db.get_match_count()}")
        return True

    except Exception as e:
        logger.error(f"Error in market matching: {e}", exc_info=True)
        return False


def run_arbitrage_scan():
    """Run arbitrage scanning phase with notifications"""
    try:
        logger.info("=" * 60)
        logger.info("PHASE 2: Arbitrage Detection")
        logger.info("=" * 60)

        # Initialize components
        db = DatabaseManager()
        detector = ArbitrageDetector()
        notifier = NotificationService()

        # Load matched markets
        matched_markets = db.get_all_matches()

        if not matched_markets:
            logger.warning("No matched markets in database. Running market matching first...")
            if not run_market_matching():
                return False
            matched_markets = db.get_all_matches()

        logger.info(f"Scanning {len(matched_markets)} matched markets...")

        # Scan for opportunities
        opportunities = detector.scan_all_matches(matched_markets)

        # Send notifications for each opportunity
        if opportunities:
            logger.info(f"Found {len(opportunities)} arbitrage opportunities!")

            for i, opp in enumerate(opportunities, 1):
                logger.info(f"\nOpportunity #{i}:")
                logger.info(f"  {opp['type']}: {opp['polymarket_question'][:60]}...")
                logger.info(f"  Net Profit: {opp['net_profit_margin']:.2%}")

                # Send notification
                notifier.send_alert(opp)

            # Send summary
            notifier.send_system_message(
                f"Scan complete: {len(opportunities)} opportunities found",
                level="success"
            )

        else:
            logger.info("No arbitrage opportunities found")
            logger.info(f"Minimum profit threshold: {config.MIN_PROFIT_MARGIN:.2%}")

        return True

    except Exception as e:
        logger.error(f"Error in arbitrage scan: {e}", exc_info=True)
        return False


def run_full_pipeline():
    """Run complete arbitrage bot pipeline"""
    try:
        logger.info("\n" + "=" * 60)
        logger.info("STARTING ARBITRAGE BOT PIPELINE")
        logger.info("=" * 60)

        start_time = time.time()

        # Phase 1: Market Matching
        success = run_market_matching()
        if not success:
            logger.error("Market matching failed, aborting pipeline")
            return

        # Phase 2: Arbitrage Detection
        run_arbitrage_scan()

        # Done
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"PIPELINE COMPLETE (took {elapsed:.1f} seconds)")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in pipeline: {e}", exc_info=True)


def run_continuous_monitoring():
    """Run bot in continuous monitoring mode"""
    logger.info("=" * 60)
    logger.info("ARBITRAGE BOT - CONTINUOUS MONITORING MODE")
    logger.info("=" * 60)
    logger.info(f"Scan interval: {config.SCAN_INTERVAL_MINUTES} minutes")
    logger.info(f"Alert method: {config.ALERT_METHOD}")
    logger.info(f"Min profit margin: {config.MIN_PROFIT_MARGIN:.2%}")
    logger.info("=" * 60)

    # Schedule regular scans
    schedule.every(config.SCAN_INTERVAL_MINUTES).minutes.do(run_full_pipeline)

    # Run immediately on startup
    run_full_pipeline()

    # Keep running
    logger.info("Bot is now monitoring for opportunities...")
    logger.info("Press Ctrl+C to stop")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nStopping bot...")
        logger.info("Goodbye!")


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "match":
            # Only run market matching
            run_market_matching()

        elif command == "scan":
            # Only run arbitrage scan
            run_arbitrage_scan()

        elif command == "monitor":
            # Run continuous monitoring
            run_continuous_monitoring()

        elif command == "once":
            # Run full pipeline once
            run_full_pipeline()

        else:
            logger.error(f"Unknown command: {command}")
            print_usage()

    else:
        # Default: run full pipeline once
        run_full_pipeline()


def print_usage():
    """Print usage instructions"""
    print("\nArbitrage Bot - Usage:")
    print("  python run.py              - Run full pipeline once")
    print("  python run.py once         - Run full pipeline once")
    print("  python run.py match        - Only fetch and match markets")
    print("  python run.py scan         - Only scan for arbitrage")
    print("  python run.py monitor      - Run continuous monitoring")
    print()


if __name__ == "__main__":
    main()
