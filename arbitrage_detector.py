"""
Arbitrage Detection Module
Detects and calculates arbitrage opportunities between Polymarket and Kalshi
"""
import logging
from typing import List, Dict, Optional
import config
from api_clients import get_polymarket_price, get_kalshi_price

logger = logging.getLogger(__name__)


class ArbitrageDetector:
    """Detects arbitrage opportunities between matched markets"""

    def __init__(
        self,
        min_profit_margin: float = None,
        kalshi_fee: float = None,
        polymarket_gas_fee: float = None
    ):
        """
        Initialize the arbitrage detector

        Args:
            min_profit_margin: Minimum profit margin to report (default from config)
            kalshi_fee: Kalshi trading fee as decimal (default from config)
            polymarket_gas_fee: Polymarket gas fee in USD (default from config)
        """
        self.min_profit_margin = min_profit_margin or config.MIN_PROFIT_MARGIN
        self.kalshi_fee = kalshi_fee or config.KALSHI_FEE_PERCENT
        self.polymarket_gas_fee = polymarket_gas_fee or config.POLYMARKET_GAS_FEE_USD

        logger.info(
            f"ArbitrageDetector initialized - Min profit: {self.min_profit_margin:.2%}, "
            f"Kalshi fee: {self.kalshi_fee:.2%}, Polymarket gas: ${self.polymarket_gas_fee}"
        )

    def check_opportunity(
        self,
        polymarket_id: str,
        kalshi_ticker: str,
        polymarket_question: str = None,
        kalshi_title: str = None
    ) -> Optional[Dict]:
        """
        Check for arbitrage opportunity on a single matched market pair

        Args:
            polymarket_id: Polymarket condition ID
            kalshi_ticker: Kalshi market ticker
            polymarket_question: Optional question text for context
            kalshi_title: Optional title text for context

        Returns:
            Dict with opportunity details or None if no opportunity
        """
        # Fetch current prices
        poly_prices = get_polymarket_price(polymarket_id)
        kalshi_prices = get_kalshi_price(kalshi_ticker)

        # Handle missing price data
        if poly_prices is None:
            logger.warning(f"Could not fetch Polymarket prices for {polymarket_id}")
            return None

        if kalshi_prices is None:
            logger.warning(f"Could not fetch Kalshi prices for {kalshi_ticker}")
            return None

        # Extract prices
        poly_yes = poly_prices["yes_price"]
        poly_no = poly_prices["no_price"]
        kalshi_yes = kalshi_prices["yes_price"]
        kalshi_no = kalshi_prices["no_price"]

        # Validate price ranges
        if not self._validate_prices(poly_yes, poly_no, kalshi_yes, kalshi_no):
            logger.warning(
                f"Invalid prices for {polymarket_id}/{kalshi_ticker}: "
                f"Poly(Y:{poly_yes}, N:{poly_no}), Kalshi(Y:{kalshi_yes}, N:{kalshi_no})"
            )
            return None

        # Check for Yes-No arbitrage (Buy Yes on Poly, No on Kalshi)
        yes_no_cost = poly_yes + kalshi_no
        yes_no_profit = 1.0 - yes_no_cost

        # Check for No-Yes arbitrage (Buy No on Poly, Yes on Kalshi)
        no_yes_cost = poly_no + kalshi_yes
        no_yes_profit = 1.0 - no_yes_cost

        # Find best opportunity
        opportunity = None

        if yes_no_profit > no_yes_profit and yes_no_profit > 0:
            # Adjust for fees
            net_profit = self._calculate_net_profit(yes_no_profit, yes_no_cost)

            if net_profit >= self.min_profit_margin:
                opportunity = {
                    "type": "Yes-No",
                    "polymarket_question": polymarket_question or poly_prices.get("question", ""),
                    "kalshi_title": kalshi_title or kalshi_prices.get("title", ""),
                    "polymarket_id": polymarket_id,
                    "kalshi_ticker": kalshi_ticker,
                    "polymarket_yes_price": poly_yes,
                    "kalshi_no_price": kalshi_no,
                    "gross_profit_margin": yes_no_profit,
                    "net_profit_margin": net_profit,
                    "total_cost": yes_no_cost,
                    "action": "Buy YES on Polymarket, NO on Kalshi"
                }

        elif no_yes_profit > 0:
            # Adjust for fees
            net_profit = self._calculate_net_profit(no_yes_profit, no_yes_cost)

            if net_profit >= self.min_profit_margin:
                opportunity = {
                    "type": "No-Yes",
                    "polymarket_question": polymarket_question or poly_prices.get("question", ""),
                    "kalshi_title": kalshi_title or kalshi_prices.get("title", ""),
                    "polymarket_id": polymarket_id,
                    "kalshi_ticker": kalshi_ticker,
                    "polymarket_no_price": poly_no,
                    "kalshi_yes_price": kalshi_yes,
                    "gross_profit_margin": no_yes_profit,
                    "net_profit_margin": net_profit,
                    "total_cost": no_yes_cost,
                    "action": "Buy NO on Polymarket, YES on Kalshi"
                }

        if opportunity:
            logger.info(
                f"Arbitrage found: {opportunity['type']} - "
                f"Net profit: {opportunity['net_profit_margin']:.2%}"
            )
        else:
            logger.debug(
                f"No arbitrage for {polymarket_id}/{kalshi_ticker}: "
                f"Yes-No: {yes_no_profit:.4f}, No-Yes: {no_yes_profit:.4f}"
            )

        return opportunity

    def scan_all_matches(self, matched_markets: List[Dict]) -> List[Dict]:
        """
        Scan all matched markets for arbitrage opportunities

        Args:
            matched_markets: List of matched market dicts with polymarket_id and kalshi_ticker

        Returns:
            List[Dict]: All found arbitrage opportunities
        """
        opportunities = []
        total_scanned = 0

        logger.info(f"Scanning {len(matched_markets)} matched markets for arbitrage")

        for match in matched_markets:
            total_scanned += 1

            try:
                opportunity = self.check_opportunity(
                    polymarket_id=match["polymarket_id"],
                    kalshi_ticker=match["kalshi_ticker"],
                    polymarket_question=match.get("polymarket_question"),
                    kalshi_title=match.get("kalshi_title")
                )

                if opportunity:
                    opportunities.append(opportunity)

                # Log progress every 10 markets
                if total_scanned % 10 == 0:
                    logger.info(f"Scanned {total_scanned}/{len(matched_markets)} markets...")

            except Exception as e:
                logger.error(
                    f"Error checking arbitrage for "
                    f"{match.get('polymarket_id')}/{match.get('kalshi_ticker')}: {e}"
                )
                continue

        logger.info(
            f"Scan complete: Found {len(opportunities)} opportunities "
            f"out of {total_scanned} markets"
        )

        return opportunities

    def _validate_prices(
        self,
        poly_yes: float,
        poly_no: float,
        kalshi_yes: float,
        kalshi_no: float
    ) -> bool:
        """
        Validate that all prices are in valid range [0, 1]

        Args:
            poly_yes, poly_no, kalshi_yes, kalshi_no: Price values

        Returns:
            bool: True if all prices valid
        """
        prices = [poly_yes, poly_no, kalshi_yes, kalshi_no]

        for price in prices:
            if price is None or not (0 <= price <= 1):
                return False

        return True

    def _calculate_net_profit(self, gross_profit: float, total_cost: float) -> float:
        """
        Calculate net profit after fees

        Args:
            gross_profit: Gross profit margin (before fees)
            total_cost: Total cost of positions

        Returns:
            float: Net profit margin after fees
        """
        # Kalshi charges fee on the winning side
        # Polymarket has gas fees
        # For simplicity, we'll subtract fees from gross profit

        kalshi_fee_amount = total_cost * self.kalshi_fee

        # Gas fee is fixed, convert to percentage based on position size
        # Assuming $100 position for calculation
        position_size = config.MAX_POSITION_USD if hasattr(config, 'MAX_POSITION_USD') else 100
        gas_fee_percent = self.polymarket_gas_fee / position_size

        total_fee_percent = kalshi_fee_amount + gas_fee_percent

        net_profit = gross_profit - total_fee_percent

        return max(0, net_profit)  # Don't return negative profits
