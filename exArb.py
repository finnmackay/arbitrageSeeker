import sqlite3
from kalshi_client.client import KalshiClient
from cryptography.hazmat.primitives import serialization
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON


KALSHI_KEY_ID = "xxx"  # Replace with your Kalshi Key ID
private_key_str = "xxx" #Replace with kalshi private key
POLY_PRIVATE_KEY = "xxx"  # Replace with your Polygon private key
POLYGON_RPC = "https://polygon-rpc.com"
USDC_CONTRACT = "xxx"
private_key = serialization.load_pem_private_key(
    private_key_str.encode(),  # Convert string to bytes
    password=None
)
kalshi_client = KalshiClient(key_id=KALSHI_KEY_ID, private_key=private_key)
polymarket_client = ClobClient(host="https://clob.polymarket.com", key=POLY_PRIVATE_KEY, chain_id=POLYGON)

def fetch_matched_markets():
    conn = sqlite3.connect("markets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matched_markets")
    matched_markets = cursor.fetchall()
    conn.close()
    return matched_markets

def check_arbitrage(poly_market_id, kalshi_ticker):
    try:
        poly_response = polymarket_client.get_market(poly_market_id)
        poly_yes_price = poly_response["tokens"][0]["price"]
        poly_no_price = poly_response["tokens"][1]["price"]
    except Exception as e:
        return None

    try:
        kalshi_response = kalshi_client.get_market(kalshi_ticker)
        kalshi_market = kalshi_response.get("market", {})
        kalshi_yes_bid = kalshi_market.get("yes_ask")
        kalshi_yes_price = float(kalshi_yes_bid / 100)
        kalshi_no_bid = kalshi_market.get("no_ask")
        kalshi_no_price = float(kalshi_no_bid / 100)
    except Exception as e:
        return None

    opportunities = []
    if poly_yes_price + kalshi_no_price < 1:
        opportunities.append({
            "Kalshi title": kalshi_market.get("title"),
            "Polymarket title": poly_response["question"],
            "type": "Yes-No",
            "polymarket_yes_price": poly_yes_price,
            "kalshi_no_price": kalshi_no_price,
            "profit_margin": 1 - (poly_yes_price + kalshi_no_price)
            })
        return opportunities


        # No-Yes Arbitrage (Kalshi Yes, Polymarket No)
    if kalshi_yes_price + poly_no_price < 1:
        opportunities.append({
            "Kalshi title": kalshi_market.get("title"),
            "Polymarket title": poly_response["question"],
            "type": "No-Yes",
            "polymarket_no_price": poly_no_price,
            "kalshi_yes_price": kalshi_yes_price,
            "profit_margin": 1 - (kalshi_yes_price + poly_no_price)
        })
        return opportunities
    return None

def main():
    # Retrieve matched markets
    matched_markets = fetch_matched_markets()
    print(f"Loaded {len(matched_markets)} matched markets from the database.")

    # Check arbitrage opportunities
    opportunities = []
    i = 0
    for market in matched_markets:
        print(i)
        i = i + 1

        arbitrage = check_arbitrage(market[3], market[4])  # polymarket_id and kalshi_ticker
        if arbitrage:
            opportunities.append(arbitrage)

    # Print results
    for opp in opportunities:
        print(f"Arbitrage Opportunity: {opp}")


if __name__ == "__main__":
    main()
