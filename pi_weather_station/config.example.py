# =============================================================================
# CONFIG TEMPLATE — Copy this to config.py and fill in your values
# =============================================================================

# Source stations to scrape (up to 3)
SOURCE_STATIONS = [
    "ILONDO760",
    # "ILONDO123",  # Uncomment and add more stations
    # "ILONDO456",
]

# Destination station (where we upload the averaged data)
WU_STATION_ID = "YOUR_STATION_ID"
WU_STATION_KEY = "YOUR_STATION_KEY"

# How often to run (seconds)
RELAY_INTERVAL = 20 * 60  # 20 minutes
