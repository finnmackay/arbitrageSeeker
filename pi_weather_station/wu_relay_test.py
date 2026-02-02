#!/usr/bin/env python3
"""
WU Relay: Scrape weather from multiple stations, average, upload.

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
# CONFIG
# =============================================================================
SOURCE_STATIONS = [
    "IANKAR46",
    "IANKAR59",
    # "ILONDO456",  # Add third station if needed
]

WU_STATION_ID = "ILONDO983"
WU_STATION_KEY = "CPBgPEJX"
WU_UPLOAD_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"
RELAY_INTERVAL = 20 * 60  # 20 minutes
# =============================================================================


def scrape_station(station_id):
    """
    Scrape latest weather from a WU station dashboard.
    Returns dict with all available fields, or None on failure.
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
    
    # === TEMPERATURE ===
    m = re.search(r'"tempAvg":\s*([\d.]+)', latest)
    if m:
        out["temp_f"] = float(m.group(1))
    else:
        m = re.search(r'"tempHigh":\s*([\d.]+)', latest)
        if m:
            out["temp_f"] = float(m.group(1))
    
    # === HUMIDITY === (outside imperial block)
    m = re.search(r'"humidityAvg":\s*([\d.]+)', latest)
    if m:
        out["humidity"] = float(m.group(1))
    
    # === PRESSURE ===
    m = re.search(r'"pressureMax":\s*([\d.]+)', latest)
    if m:
        out["baromin"] = float(m.group(1))
    
    # === DEWPOINT ===
    m = re.search(r'"dewptAvg":\s*([\d.]+)', latest)
    if m:
        out["dewpt_f"] = float(m.group(1))
    
    # === WIND SPEED ===
    m = re.search(r'"windspeedAvg":\s*([\d.]+)', latest)
    if m:
        out["windspeed_mph"] = float(m.group(1))
    
    # === WIND GUST ===
    m = re.search(r'"windgustHigh":\s*([\d.]+)', latest)
    if m:
        out["windgust_mph"] = float(m.group(1))
    
    # === WIND DIRECTION === (outside imperial block)
    m = re.search(r'"winddirAvg":\s*([\d.]+)', latest)
    if m:
        out["winddir"] = int(float(m.group(1)))
    
    # === PRECIP RATE ===
    m = re.search(r'"precipRate":\s*([\d.]+)', latest)
    if m:
        out["precip_rate"] = float(m.group(1))
    
    # === PRECIP TOTAL (daily) ===
    m = re.search(r'"precipTotal":\s*([\d.]+)', latest)
    if m:
        out["precip_daily"] = float(m.group(1))
    
    # === UV INDEX === (can be null)
    m = re.search(r'"uvHigh":\s*([\d.]+)', latest)
    if m:
        out["uv"] = float(m.group(1))
    
    if not out.get("temp_f"):
        print(f"  [{station_id}] No temperature found")
        return None
    
    return out


def scrape_and_average():
    """
    Scrape all source stations and return averaged values.
    Returns (averaged_dict, count) or None if all fail.
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
    
    # Average all fields
    avg = {}
    
    # Helper to average a field across readings
    def avg_field(key):
        vals = [r[key] for r in readings if r.get(key) is not None]
        return sum(vals) / len(vals) if vals else None
    
    avg["temp_f"] = avg_field("temp_f")
    avg["humidity"] = avg_field("humidity")
    avg["baromin"] = avg_field("baromin")
    avg["dewpt_f"] = avg_field("dewpt_f")
    avg["windspeed_mph"] = avg_field("windspeed_mph")
    avg["windgust_mph"] = avg_field("windgust_mph")
    avg["winddir"] = avg_field("winddir")
    avg["precip_rate"] = avg_field("precip_rate")
    avg["precip_daily"] = avg_field("precip_daily")
    avg["uv"] = avg_field("uv")
    
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
        "action": "updateraw",
    }
    
    # Required
    if obs.get("temp_f") is not None:
        params["tempf"] = f"{obs['temp_f']:.1f}"
    
    # Optional fields
    if obs.get("humidity") is not None:
        params["humidity"] = f"{obs['humidity']:.0f}"
    
    if obs.get("baromin") is not None:
        params["baromin"] = f"{obs['baromin']:.2f}"
    
    if obs.get("dewpt_f") is not None:
        params["dewptf"] = f"{obs['dewpt_f']:.1f}"
    
    if obs.get("windspeed_mph") is not None:
        params["windspeedmph"] = f"{obs['windspeed_mph']:.1f}"
    
    if obs.get("windgust_mph") is not None:
        params["windgustmph"] = f"{obs['windgust_mph']:.1f}"
    
    if obs.get("winddir") is not None:
        params["winddir"] = f"{obs['winddir']:.0f}"
    
    if obs.get("precip_rate") is not None:
        params["rainin"] = f"{obs['precip_rate']:.2f}"
    
    if obs.get("precip_daily") is not None:
        params["dailyrainin"] = f"{obs['precip_daily']:.2f}"
    
    if obs.get("uv") is not None:
        params["UV"] = f"{obs['uv']:.1f}"
    
    url = f"{WU_UPLOAD_URL}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            body = resp.read().decode("utf-8").strip()
            return body == "success", body
    except Exception as e:
        return False, str(e)


def format_obs(obs):
    """Format observation for display."""
    parts = []
    if obs.get("temp_f") is not None:
        temp_c = (obs["temp_f"] - 32) * 5 / 9
        parts.append(f"{obs['temp_f']:.1f}°F ({temp_c:.1f}°C)")
    if obs.get("humidity") is not None:
        parts.append(f"humidity={obs['humidity']:.0f}%")
    if obs.get("windspeed_mph") is not None:
        parts.append(f"wind={obs['windspeed_mph']:.1f}mph")
    if obs.get("baromin") is not None:
        parts.append(f"pressure={obs['baromin']:.2f}\"")
    return " | ".join(parts) if parts else "no data"


def main():
    once = "--once" in sys.argv
    
    print("=" * 60)
    print(f"WU RELAY: {len(SOURCE_STATIONS)} station(s) → {WU_STATION_ID}")
    print(f"Sources: {', '.join(SOURCE_STATIONS)}")
    print(f"Interval: {RELAY_INTERVAL // 60} min" if not once else "Mode: single run")
    print("=" * 60)
    
    while True:
        print(f"\n[{datetime.now():%H:%M:%S}] Scraping {len(SOURCE_STATIONS)} station(s)...")
        
        result = scrape_and_average()
        
        if not result:
            print(f"[{datetime.now():%H:%M:%S}] All stations failed to scrape")
        else:
            avg, count = result
            
            success, response = upload_weather(avg)
            
            if success:
                print(f"[{datetime.now():%H:%M:%S}] AVG from {count} station(s): {format_obs(avg)} → uploaded OK")
            else:
                print(f"[{datetime.now():%H:%M:%S}] Upload failed: {response}")
        
        if once:
            break
        time.sleep(RELAY_INTERVAL)


if __name__ == "__main__":
    main()
