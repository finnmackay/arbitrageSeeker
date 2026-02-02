#!/usr/bin/env python3
"""
Weather Data Pipeline
Shows the complete data flow: Raw readings → Averaging → WU Upload
"""
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# =============================================================================
# 1. RAW TEMPERATURE LOG (from Pi sensor)
# =============================================================================
# Each reading from the Pi gets logged here

RAW_LOG_FILE = "raw_readings.jsonl"

def log_raw_reading(temp_c: float, source: str = "pi_sensor"):
    """
    Log a single raw reading from the Pi

    Example entry:
    {
        "temp_c": 7.24,
        "temp_f": 45.03,
        "source": "pi_sensor",
        "timestamp_utc": "2026-01-30T14:30:00.000000",
        "timestamp_local": "2026-01-30T14:30:00.000000"
    }
    """
    entry = {
        "temp_c": round(temp_c, 2),
        "temp_f": round((temp_c * 9/5) + 32, 2),
        "source": source,
        "timestamp_utc": datetime.utcnow().isoformat(),
        "timestamp_local": datetime.now().isoformat()
    }

    with open(RAW_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


# =============================================================================
# 2. AVERAGING (last N minutes of readings)
# =============================================================================

AVERAGED_LOG_FILE = "averaged_readings.jsonl"

def load_recent_readings(minutes: int = 5) -> list:
    """Load readings from the last N minutes"""
    if not Path(RAW_LOG_FILE).exists():
        return []

    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    recent = []

    with open(RAW_LOG_FILE, "r") as f:
        for line in f:
            entry = json.loads(line)
            entry_time = datetime.fromisoformat(entry["timestamp_utc"])
            if entry_time > cutoff:
                recent.append(entry)

    return recent


def calculate_average(readings: list) -> dict:
    """
    Calculate averaged data from recent readings

    Example output:
    {
        "avg_temp_c": 7.35,
        "avg_temp_f": 45.23,
        "min_temp_c": 7.12,
        "max_temp_c": 7.58,
        "reading_count": 5,
        "period_minutes": 5,
        "calculated_at_utc": "2026-01-30T14:35:00.000000"
    }
    """
    if not readings:
        return None

    temps_c = [r["temp_c"] for r in readings]

    averaged = {
        "avg_temp_c": round(sum(temps_c) / len(temps_c), 2),
        "avg_temp_f": round(((sum(temps_c) / len(temps_c)) * 9/5) + 32, 2),
        "min_temp_c": round(min(temps_c), 2),
        "max_temp_c": round(max(temps_c), 2),
        "reading_count": len(readings),
        "period_minutes": 5,
        "calculated_at_utc": datetime.utcnow().isoformat()
    }

    # Log the averaged reading
    with open(AVERAGED_LOG_FILE, "a") as f:
        f.write(json.dumps(averaged) + "\n")

    return averaged


# =============================================================================
# 3. WEATHER UNDERGROUND UPLOAD
# =============================================================================

WU_STATION_ID = "ILONDO983"
WU_STATION_KEY = "CPBgPEJX"
WU_UPLOAD_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
WU_UPLOAD_LOG = "wu_uploads.jsonl"

def prepare_wu_payload(averaged_data: dict) -> dict:
    """
    Prepare the final payload for Weather Underground

    WU expects these URL parameters:
    {
        "ID": "ILONDO983",
        "PASSWORD": "CPBgPEJX",
        "dateutc": "now",
        "tempf": "45.23",
        "action": "updateraw"
    }

    Optional fields you can add:
    - humidity: "80"
    - dewptf: "39.2"
    - baromin: "30.12"
    - winddir: "180"
    - windspeedmph: "5.5"
    - rainin: "0.0"
    """
    payload = {
        "ID": WU_STATION_ID,
        "PASSWORD": WU_STATION_KEY,
        "dateutc": "now",
        "tempf": str(averaged_data["avg_temp_f"]),
        "action": "updateraw"
    }

    return payload


def upload_to_wu(payload: dict) -> dict:
    """
    Upload to Weather Underground and log the result

    Example log entry:
    {
        "payload": {"ID": "ILONDO983", "PASSWORD": "***", "tempf": "45.23", ...},
        "response": "success",
        "success": true,
        "uploaded_at_utc": "2026-01-30T14:35:00.000000",
        "wu_url": "https://weatherstation.wunderground.com/..."
    }
    """
    try:
        response = requests.get(WU_UPLOAD_URL, params=payload, timeout=10)
        success = response.text.strip() == "success"
    except Exception as e:
        response = None
        success = False

    # Log the upload attempt (hide password in log)
    log_entry = {
        "payload": {**payload, "PASSWORD": "***"},
        "response": response.text.strip() if response else "error",
        "success": success,
        "uploaded_at_utc": datetime.utcnow().isoformat(),
        "wu_url": f"{WU_UPLOAD_URL}?ID={payload['ID']}&tempf={payload['tempf']}&..."
    }

    with open(WU_UPLOAD_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return log_entry


# =============================================================================
# FULL PIPELINE
# =============================================================================

def run_pipeline(temp_c: float):
    """
    Complete pipeline: Log → Average → Upload

    Returns summary of what happened at each stage
    """
    print("\n" + "=" * 60)
    print("WEATHER DATA PIPELINE")
    print("=" * 60)

    # Step 1: Log raw reading
    raw = log_raw_reading(temp_c)
    print(f"\n1. RAW READING LOGGED:")
    print(f"   File: {RAW_LOG_FILE}")
    print(f"   Data: {json.dumps(raw, indent=2)}")

    # Step 2: Calculate average
    recent = load_recent_readings(minutes=5)
    averaged = calculate_average(recent)
    print(f"\n2. AVERAGED DATA:")
    print(f"   File: {AVERAGED_LOG_FILE}")
    print(f"   Readings in last 5 min: {len(recent)}")
    print(f"   Data: {json.dumps(averaged, indent=2)}")

    # Step 3: Prepare and upload to WU
    if averaged:
        payload = prepare_wu_payload(averaged)
        print(f"\n3. WU UPLOAD PAYLOAD:")
        print(f"   {json.dumps({**payload, 'PASSWORD': '***'}, indent=2)}")

        result = upload_to_wu(payload)
        print(f"\n4. WU UPLOAD RESULT:")
        print(f"   File: {WU_UPLOAD_LOG}")
        print(f"   Success: {result['success']}")
        print(f"   Response: {result['response']}")

    print("\n" + "=" * 60)

    return {
        "raw": raw,
        "averaged": averaged,
        "uploaded": result if averaged else None
    }


# =============================================================================
# EXAMPLE / TEST
# =============================================================================

if __name__ == "__main__":
    # Simulate some readings
    print("Simulating temperature readings...")

    import time
    import random

    # Add a few readings to build up average
    for i in range(3):
        temp = 7.0 + random.uniform(-0.5, 0.5)  # 6.5 to 7.5°C
        log_raw_reading(temp)
        print(f"Logged reading {i+1}: {temp:.2f}°C")
        time.sleep(1)

    # Now run full pipeline with a new reading
    final_temp = 7.2
    result = run_pipeline(final_temp)

    print("\n\nFILE CONTENTS:")
    print("-" * 40)

    for fname in [RAW_LOG_FILE, AVERAGED_LOG_FILE, WU_UPLOAD_LOG]:
        if Path(fname).exists():
            print(f"\n{fname}:")
            with open(fname) as f:
                for line in f:
                    print(f"  {line.strip()}")
