import sqlite3
from kalshi_client.client import KalshiClient
from cryptography.hazmat.primitives import serialization
from py_clob_client.client import ClobClient
from py_clob_client.constants import POLYGON
from sentence_transformers import SentenceTransformer, util
import re


def extract_numbers(text):
    return re.findall(r'\d+', text)  # Matches any sequence of digits
def extract_names(text):
    return re.findall(r'\b[A-Z][a-z]*\b', text[1:len(text) - 1])  # Matches capitalized words

KALSHI_KEY_ID = "xxx"  # Replace with your Kalshi Key ID
private_key_str = "xxx"  # Replace with your Kalshi private key file path
POLY_PRIVATE_KEY = "xxx"  # Replace with your Polygon private key
POLYGON_RPC = "https://polygon-rpc.com"
USDC_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

def setup_database():
    conn = sqlite3.connect("markets.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matched_markets (
            id INTEGER PRIMARY KEY,
            polymarket_question TEXT,
            kalshi_title TEXT,
            polymarket_id TEXT,
            kalshi_ticker TEXT
        )
    """)
    conn.commit()
    return conn

# Fetch Polymarket markets with pagination
def fetch_polymarket_markets():
    all_markets = []
    next_cursor = ""
    limit = 100

    while True:
        response = polymarket_client.get_markets(next_cursor=next_cursor)
        if "data" in response:
            all_markets.extend(response["data"])
        next_cursor = response.get("next_cursor")
        if next_cursor == "LTE=" or not next_cursor:
            break
    return all_markets

# Fetch Kalshi markets with pagination
def fetch_kalshi_markets():
    all_markets = []
    cursor = None
    limit = 100

    while True:
        response = kalshi_client.get_markets(cursor=cursor, limit=limit,status="open")
        if "markets" in response:
            all_markets.extend(response["markets"])
        cursor = response.get("cursor")
        if not cursor:
            break
    return all_markets





# Load the SentenceTransformer model
model = SentenceTransformer('all-mpnet-base-v2')  # Lightweight model for fast performance

def find_best_matches(poly_markets, kalshi_markets, similarity_threshold=0.9):
    """
    Use SentenceTransformers to find the best matching markets based on semantic similarity.
    """
    matches = []

    # Encode all market questions and titles
    poly_questions = [p_market["question"] for p_market in poly_markets if "question" in p_market]
    kalshi_titles = ["" + k_market["title"] + k_market["subtitle"] for k_market in kalshi_markets if "title" in k_market]

    poly_embeddings = model.encode(poly_questions, convert_to_tensor=True)
    kalshi_embeddings = model.encode(kalshi_titles, convert_to_tensor=True)

    # Compute pairwise cosine similarities
    similarities = util.cos_sim(poly_embeddings, kalshi_embeddings)

    # Find the best match for each Polymarket question
    for i, p_market in enumerate(poly_markets):
        if "question" not in p_market:
            continue

        # Get similarity scores for the current Polymarket question
        similarity_scores = similarities[i].tolist()

        # Find the best matching Kalshi market
        best_match_index = max(range(len(similarity_scores)), key=lambda j: similarity_scores[j])
        best_match_score = similarity_scores[best_match_index]

        # Append if it meets the threshold
        if best_match_score >= similarity_threshold:
            matches.append({
                "polymarket_question": p_market["question"],
                "kalshi_title": kalshi_markets[best_match_index]["title"],
                "polymarket_id": p_market.get("condition_id"),
                "kalshi_ticker": kalshi_markets[best_match_index].get("ticker"),
                "similarity_score": best_match_score
            })

    print(f"Found {len(matches)} best matches using SentenceTransformers.")
    return matches




# Store matches in the database
def store_matches(matches, conn):
    cursor = conn.cursor()
    for match in matches:
        cursor.execute("""
            INSERT INTO matched_markets (polymarket_question, kalshi_title, polymarket_id, kalshi_ticker)
            VALUES (?, ?, ?, ?)
        """, (match["polymarket_question"], match["kalshi_title"], match["polymarket_id"], match["kalshi_ticker"]))
    conn.commit()

# Main script
if __name__ == "__main__":
    private_key = serialization.load_pem_private_key(
        private_key_str.encode(),  # Convert string to bytes
        password=None
    )
    kalshi_client = KalshiClient(key_id=KALSHI_KEY_ID, private_key=private_key)
    polymarket_client = ClobClient(host="https://clob.polymarket.com", key=POLY_PRIVATE_KEY, chain_id=POLYGON)

    # Set up database
    conn = setup_database()

    # Fetch markets
    poly_markets = fetch_polymarket_markets()
    kalshi_markets = fetch_kalshi_markets()

    # Find and store matches
    matches = find_best_matches(poly_markets, kalshi_markets)
    store_matches(matches, conn)
    print(f"Stored {len(matches)} matched markets in the database.")

    conn.close()




