#!/usr/bin/env python3
"""
WU Relay: Scrape weather from ILONDO760 → Upload to ILONDO983 every 20 min.

Run: python3 wu_relay_test.py          # loop every 20 min
Run: python3 wu_relay_test.py --once   # single run then exit
"""
import re
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime

# Config
SOURCE_URL = "https://www.wunderground.com/dashboard/pws/ILONDO760"
WU_STATION_ID = "ILONDO983"
WU_STATION_KEY = "CPBgPEJX"
WU_UPLOAD_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
RELAY_INTERVAL = 20 * 60  # 20 minutes


def scrape_weather():
    """
    Scrape latest weather from ILONDO760 dashboard.
    Returns dict with temp_f, humidity, baromin (any can be None).
    """
    # Fetch page
    req = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    
    # Find observations array and get the LAST (most recent) entry
    m = re.search(r'"observations":\s*\[(.+?)\]\s*[,}]', html, re.DOTALL)
    if not m:
        return None
    
    # Each observation looks like: {"stationID"... "imperial":{...}}
    obs_matches = re.findall(r'\{"stationID"[^}]+?"imperial":\s*\{[^}]+\}\}', m.group(1))
    if not obs_matches:
        return None
    
    latest = obs_matches[-1]  # Most recent observation
    
    # Extract values from the imperial block
    out = {}
    
    # Temperature (use tempAvg or tempHigh)
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
        out["humidity"] = int(float(m.group(1)))
    
    # Pressure
    m = re.search(r'"pressureM(?:ax|in)":\s*([\d.]+)', latest)
    if m:
        out["baromin"] = float(m.group(1))
    
    return out if out.get("temp_f") else None


def upload_weather(obs):
    """
    Upload weather observation to ILONDO983.
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
    print("WU RELAY: ILONDO760 → ILONDO983")
    print(f"Interval: {RELAY_INTERVAL // 60} min" if not once else "Mode: single run")
    print("=" * 50)
    
    while True:
        obs = scrape_weather()
        
        if not obs:
            print(f"[{datetime.now():%H:%M:%S}] Failed to scrape weather")
        else:
            success, response = upload_weather(obs)
            temp_c = (obs["temp_f"] - 32) * 5 / 9
            
            if success:
                print(f"[{datetime.now():%H:%M:%S}] {obs['temp_f']:.1f}°F ({temp_c:.1f}°C) → uploaded OK")
            else:
                print(f"[{datetime.now():%H:%M:%S}] Upload failed: {response}")
        
        if once:
            break
        time.sleep(RELAY_INTERVAL)


if __name__ == "__main__":
    main()
