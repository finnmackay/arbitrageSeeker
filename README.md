# Event-Based Arbitrage Bot

This project identifies arbitrage opportunities between **Polymarket** and **Kalshi** by fetching matched markets from a database, retrieving live market data using APIs, and checking for profitable trades. It includes a simple UI for reviewing matches and calculating payouts for selected trades.

----------

## Features

-   **Fetch Matches**:
    
    -   Retrieves matched market IDs (Polymarket `condition_id` and Kalshi `ticker`) from a local SQLite database.
-   **Dynamic Market Data Retrieval**:
    
    -   Fetches live market data using Polymarket and Kalshi APIs.
-   **Arbitrage Opportunity Detection**:
    
    -   Checks for Yes/No and No/Yes arbitrage opportunities using real-time market prices.
-   **User-Friendly UI**:
    
    -   Displays matched markets and allows manual review, trade confirmation, and payout calculation.
-   **Profit Margin Calculation**:
    
    -   Calculates potential profits based on entered trade amounts and market odds.

----------

## Requirements

### **Dependencies**

Install the required Python libraries using pip:

bash

CopyEdit

`pip install sentence-transformers
pip install py-clob-client
pip install kalshi-client
pip install cryptography` 

### **Environment**

-   Python 3.8+
-   SQLite database (`markets.db`) for storing matched markets.
