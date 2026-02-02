#!/usr/bin/env python3
"""
WU Relay: Scrape weather from multiple stations, average, upload to ILONDO983.

Run: python3 wu_relay_test.py          # loop every 20 min
Run: python3 wu_relay_test.py --once   # single run then exit
"""
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime

# =============================================================================
# CONFIG — Add up to 3 source stations here
# =============================================================================
SOURCE_STATIONS = [
    "ILONDO760",
    # "ILONDO123",  # Uncomment and replace to add more stations
    # "ILONDO456",
]

# Destination station (where we upload the averaged data)
WU_STATION_ID = "ILONDO983"
WU_STATION_KEY = "CPBgPEJX"
WU_UPLOAD_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

# How often to run (seconds)
RELAY_INTERVAL = 20 * 60  # 20 minutes
# =============================================================================


def scrape_station(station_id):
    """
    Scrape latest weather from a WU station dashboard.
    Returns dict with temp_f, humidity, baromin (any can be None), or None on failure.
    """
    url = f"https://www.wunderground.com/dashboard/pws/{station_id}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [{station_id}] Fetch error: {e}")
        return None
    
    # Find observations array and get the LAST (most recent) entry
    m = re.search(r'"observations":\s*\[(.+?)\]\s*[,}]', html, re.DOTALL)
    if not m:
        print(f"  [{station_id}] No observations found")
        return None
    
    obs_matches = re.findall(r'\{"stationID"[^}]+?"imperial":\s*\{[^}]+\}\}', m.group(1))
    if not obs_matches:
        print(f"  [{station_id}] No observation data")
        return None
    
    latest = obs_matches[-1]
    out = {}
    
    # Temperature
    m = re.search(r'"tempAvg":\s*([\d.]+)', latest)
    if m:
        out["temp_f"] = float(m.group(1))
    else:
        m = re.search(r'"tempHigh":\s*([\d.]+)', latest)
        if m:
            out["temp_f"] = float(m.group(1))
    
    # Humidity
    m = re.search(r'"humidityAvg":\s*([\d.]+)', latest)
    if m:
        out["humidity"] = float(m.group(1))
    
    # Pressure
    m = re.search(r'"pressureM(?:ax|in)":\s*([\d.]+)', latest)
    if m:
        out["baromin"] = float(m.group(1))
    
    if not out.get("temp_f"):
        print(f"  [{station_id}] No temperature found")
        return None
    
    return out


def scrape_and_average():
    """
    Scrape all source stations and return averaged values.
    Returns dict with temp_f, humidity, baromin (averaged), or None if all fail.
    """
    readings = []
    
    for station_id in SOURCE_STATIONS:
        obs = scrape_station(station_id)
        if obs:
            readings.append(obs)
            temp_c = (obs["temp_f"] - 32) * 5 / 9
            print(f"  [{station_id}] {obs['temp_f']:.1f}°F ({temp_c:.1f}°C)")
    
    if not readings:
        return None
    
    # Average the values
    avg = {}
    
    # Temperature (required)
    temps = [r["temp_f"] for r in readings]
    avg["temp_f"] = sum(temps) / len(temps)
    
    # Humidity (optional)
    humidities = [r["humidity"] for r in readings if r.get("humidity")]
    if humidities:
        avg["humidity"] = int(sum(humidities) / len(humidities))
    
    # Pressure (optional)
    pressures = [r["baromin"] for r in readings if r.get("baromin")]
    if pressures:
        avg["baromin"] = sum(pressures) / len(pressures)
    
    return avg, len(readings)


def upload_weather(obs):
    """
    Upload weather observation to destination station.
    Returns (success: bool, response: str).
    """
    params = {
        "ID": WU_STATION_ID,
        "PASSWORD": WU_STATION_KEY,
        "dateutc": "now",
        "tempf": f"{obs['temp_f']:.1f}",
        "action": "updateraw",
    }
    if obs.get("humidity"):
        params["humidity"] = str(obs["humidity"])
    if obs.get("baromin"):
        params["baromin"] = f"{obs['baromin']:.2f}"
    
    url = f"{WU_UPLOAD_URL}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode("utf-8").strip()
            return body == "success", body
    except Exception as e:
        return False, str(e)


def main():
    once = "--once" in sys.argv
    
    print("=" * 50)
    print(f"WU RELAY: {len(SOURCE_STATIONS)} station(s) → {WU_STATION_ID}")
    print(f"Sources: {', '.join(SOURCE_STATIONS)}")
    print(f"Interval: {RELAY_INTERVAL // 60} min" if not once else "Mode: single run")
    print("=" * 50)
    
    while True:
        print(f"\n[{datetime.now():%H:%M:%S}] Scraping {len(SOURCE_STATIONS)} station(s)...")
        
        result = scrape_and_average()
        
        if not result:
            print(f"[{datetime.now():%H:%M:%S}] All stations failed to scrape")
        else:
            avg, count = result
            temp_c = (avg["temp_f"] - 32) * 5 / 9
            
            success, response = upload_weather(avg)
            
            if success:
                print(f"[{datetime.now():%H:%M:%S}] AVG from {count} station(s): {avg['temp_f']:.1f}°F ({temp_c:.1f}°C) → uploaded OK")
            else:
                print(f"[{datetime.now():%H:%M:%S}] Upload failed: {response}")
        
        if once:
            break
        time.sleep(RELAY_INTERVAL)


if __name__ == "__main__":
    main()
