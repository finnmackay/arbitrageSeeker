#!/usr/bin/env python3
"""
Upload historical temperature data to Weather Underground
Pull from database/file and backfill to WU with original timestamps
"""
import requests
import json
import time
from datetime import datetime
from pathlib import Path

# Weather Underground
WU_STATION_ID = "ILONDO983"
WU_STATION_KEY = "CPBgPEJX"
WU_UPLOAD_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

# Rate limiting - WU may block if you upload too fast
DELAY_BETWEEN_UPLOADS = 2  # seconds


def format_dateutc(timestamp: datetime) -> str:
    """
    Format timestamp for WU API

    WU expects: YYYY-MM-DD+HH:MM:SS (URL encoded space)
    Example: 2026-01-30+14:30:00
    """
    return timestamp.strftime("%Y-%m-%d+%H:%M:%S")


def upload_historic_reading(temp_c: float, timestamp: datetime) -> dict:
    """
    Upload a single historic reading to WU

    Payload example:
    {
        "ID": "ILONDO983",
        "PASSWORD": "CPBgPEJX",
        "dateutc": "2026-01-30+14:30:00",
        "tempf": "45.03",
        "action": "updateraw"
    }
    """
    temp_f = (temp_c * 9/5) + 32

    payload = {
        "ID": WU_STATION_ID,
        "PASSWORD": WU_STATION_KEY,
        "dateutc": format_dateutc(timestamp),
        "tempf": f"{temp_f:.1f}",
        "action": "updateraw"
    }

    try:
        response = requests.get(WU_UPLOAD_URL, params=payload, timeout=10)
        success = response.text.strip() == "success"
    except Exception as e:
        print(f"Error: {e}")
        success = False
        response = None

    return {
        "timestamp": timestamp.isoformat(),
        "temp_c": temp_c,
        "success": success,
        "response": response.text.strip() if response else "error"
    }


def backfill_from_jsonl(filepath: str):
    """
    Read historic readings from JSONL file and upload to WU

    Expected format (one per line):
    {"temp_c": 7.24, "timestamp_utc": "2026-01-30T14:30:00"}
    """
    if not Path(filepath).exists():
        print(f"File not found: {filepath}")
        return

    print(f"Backfilling from {filepath}")
    print("=" * 50)

    uploaded = 0
    failed = 0

    with open(filepath, "r") as f:
        for line in f:
            entry = json.loads(line)
            temp_c = entry["temp_c"]
            timestamp = datetime.fromisoformat(entry["timestamp_utc"])

            result = upload_historic_reading(temp_c, timestamp)

            if result["success"]:
                print(f"✓ {timestamp} | {temp_c:.1f}°C | uploaded")
                uploaded += 1
            else:
                print(f"✗ {timestamp} | {temp_c:.1f}°C | {result['response']}")
                failed += 1

            time.sleep(DELAY_BETWEEN_UPLOADS)

    print("=" * 50)
    print(f"Done: {uploaded} uploaded, {failed} failed")


def backfill_from_postgres(connection_string: str, start_date: str, end_date: str):
    """
    Pull historic readings from PostgreSQL and upload to WU

    Table schema expected:
    CREATE TABLE temperature_readings (
        id SERIAL PRIMARY KEY,
        temp_c FLOAT NOT NULL,
        timestamp_utc TIMESTAMP NOT NULL
    );
    """
    import psycopg2

    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()

    cur.execute("""
        SELECT temp_c, timestamp_utc
        FROM temperature_readings
        WHERE timestamp_utc BETWEEN %s AND %s
        ORDER BY timestamp_utc
    """, (start_date, end_date))

    rows = cur.fetchall()
    print(f"Found {len(rows)} readings to backfill")
    print("=" * 50)

    uploaded = 0
    failed = 0

    for temp_c, timestamp in rows:
        result = upload_historic_reading(temp_c, timestamp)

        if result["success"]:
            print(f"✓ {timestamp} | {temp_c:.1f}°C | uploaded")
            uploaded += 1
        else:
            print(f"✗ {timestamp} | {temp_c:.1f}°C | {result['response']}")
            failed += 1

        time.sleep(DELAY_BETWEEN_UPLOADS)

    cur.close()
    conn.close()

    print("=" * 50)
    print(f"Done: {uploaded} uploaded, {failed} failed")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Option 1: Backfill from local JSONL file
    # backfill_from_jsonl("raw_readings.jsonl")

    # Option 2: Backfill from PostgreSQL
    # backfill_from_postgres(
    #     connection_string="postgresql://user:pass@host:5432/dbname",
    #     start_date="2026-01-30 00:00:00",
    #     end_date="2026-01-30 23:59:59"
    # )

    # Test single historic upload
    print("Testing historic upload...")
    test_time = datetime(2026, 1, 30, 10, 30, 0)  # 10:30 AM on Jan 30
    result = upload_historic_reading(temp_c=7.5, timestamp=test_time)
    print(f"Result: {json.dumps(result, indent=2)}")
