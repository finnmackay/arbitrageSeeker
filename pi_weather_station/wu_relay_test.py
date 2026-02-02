#!/usr/bin/env python3
"""
Pull weather from ILONDO760 (old station) dashboard and re-upload to ILONDO983
(your station) every 20 minutes so ILONDO983 shows that data.

Source: ILONDO760 dashboard (old station).
Destination: ILONDO983, key CPBgPEJX (the station you upload to).

Run: python3 wu_relay_test.py          # loop every 20 min
Run: python3 wu_relay_test.py --once  # fetch once, upload, exit
"""
import re
import sys
import json
import time
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

# Optional: load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Source: old station — we pull data from its dashboard
SOURCE_STATION = "ILONDO760"
SOURCE_URL = "https://www.wunderground.com/dashboard/pws/ILONDO760"

# Destination: your station — upload TO ILONDO983 (key for this station)
WU_STATION_ID = "ILONDO983"
WU_STATION_KEY = "CPBgPEJX"
WU_UPLOAD_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

# How often to fetch and re-upload (seconds) — 20 minutes
RELAY_INTERVAL = 20 * 60


def fetch_dashboard_html(url: str) -> str:
    """Fetch dashboard page with a browser-like User-Agent."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_json_from_page(html: str) -> Optional[dict]:
    """
    Try to find embedded JSON in the dashboard page (e.g. __NEXT_DATA__, __NUXT__, or similar).
    Returns first parsed JSON blob that looks like weather data, or None.
    """
    # Common patterns for embedded JSON
    patterns = [
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        r'__NUXT_DATA__\s*=\s*(\{.*?\});',
        r'"current_observation"\s*:\s*(\{.*?\})\s*[,}]',
        r'"stationId"\s*:\s*"[^"]*"\s*,\s*"metric"\s*:\s*(\{.*?\})\s*[,}]',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                return data
            except json.JSONDecodeError:
                continue
    return None


def extract_latest_observation(html: str) -> Dict[str, Any]:
    """
    Extract the LATEST observation from the observations array embedded in the page.
    WU embeds hourly observations; we want the most recent one for "right now" data.
    Returns dict with temp_f, humidity, baromin (any can be missing).
    """
    out: Dict[str, Any] = {}
    
    # Find the observations array - it contains multiple hourly readings
    # Each observation has obsTimeUtc and imperial block with tempHigh/tempAvg
    m = re.search(r'"observations":\s*\[(.+?)\]\s*[,}]', html, re.DOTALL)
    if not m:
        return out
    
    obs_text = m.group(1)
    
    # Find all individual observations (each starts with {"stationID")
    obs_matches = re.findall(r'\{"stationID"[^}]+?"imperial":\s*\{[^}]+\}\}', obs_text)
    
    if not obs_matches:
        return out
    
    # Get the LAST observation (most recent)
    latest = obs_matches[-1]
    
    # Extract temp from imperial block - use tempAvg as "current" (or tempHigh)
    m = re.search(r'"tempAvg":\s*([\d.]+)', latest)
    if m:
        out["temp_f"] = float(m.group(1))
    elif re.search(r'"tempHigh":\s*([\d.]+)', latest):
        m = re.search(r'"tempHigh":\s*([\d.]+)', latest)
        out["temp_f"] = float(m.group(1))
    
    # Extract humidity
    m = re.search(r'"humidityAvg":\s*([\d.]+)', latest)
    if m:
        out["humidity"] = int(float(m.group(1)))
    
    # Extract pressure
    m = re.search(r'"pressureM(?:ax|in)":\s*([\d.]+)', latest)
    if m:
        out["baromin"] = float(m.group(1))
    
    return out


def extract_summary_from_table(html: str) -> Dict[str, Any]:
    """
    Parse the Summary table on the dashboard. Returns dict with temp_f, humidity, baromin.
    We explicitly use the THIRD column (Average) for temp/humidity — not the first (High),
    which was giving ~11°C instead of current-ish ~9°C.
    """
    out: Dict[str, Any] = {}
    # Temperature: "Temperature | 52.7 °F | 38.5 °F | 44.8 °F" (High | Low | Average) → use 3rd
    m = re.search(
        r'Temperature\s*\|[^|]*\|\s*([\d.]+)\s*°?\s*F\s*\|[^|]*\|\s*([\d.]+)\s*°?\s*F\s*\|[^|]*\|\s*([\d.]+)\s*°?\s*F',
        html, re.IGNORECASE
    )
    if not m:
        # Fallback: any three numbers after "Temperature |" — use 3rd (Average)
        m = re.search(r'Temperature\s*\|[^|]*\|\s*([\d.]+)[^|]*\|[^|]*\|\s*([\d.]+)[^|]*\|[^|]*\|\s*([\d.]+)', html, re.IGNORECASE)
    if m:
        # Column order: 1=High, 2=Low, 3=Average — use Average (closest to "current")
        out["temp_f"] = float(m.group(3))
    # Humidity: same idea — use third column (Average)
    m = re.search(
        r'Humidity\s*\|[^|]*\|\s*([\d.]+)\s*°?%\s*\|[^|]*\|\s*([\d.]+)\s*°?%\s*\|[^|]*\|\s*([\d.]+)\s*°?%',
        html, re.IGNORECASE
    )
    if m:
        out["humidity"] = int(float(m.group(3)))
    # Pressure: "Pressure | 29.46 °in | 29.29 °in | --" — use middle (Low) or first; avoid --
    m = re.search(
        r'Pressure\s*\|[^|]*\|\s*([\d.]+)\s*°?in\s*\|[^|]*\|\s*([\d.]+)\s*°?in',
        html, re.IGNORECASE
    )
    if m:
        out["baromin"] = float(m.group(2))  # second value (e.g. 29.29) as proxy for current
    elif re.search(r'Pressure\s*\|[^|]*\|\s*([\d.]+)\s*°?in', html, re.IGNORECASE):
        m2 = re.search(r'Pressure\s*\|[^|]*\|\s*([\d.]+)\s*°?in', html, re.IGNORECASE)
        if m2:
            out["baromin"] = float(m2.group(1))
    return out


def _get_obs(obj: dict) -> Optional[Dict[str, Any]]:
    """Extract temp_f, humidity, baromin from a single observation object."""
    out: Dict[str, Any] = {}
    # Imperial / temp_f
    if "temp_f" in obj:
        out["temp_f"] = float(obj["temp_f"])
    elif "imperial" in obj and isinstance(obj["imperial"], dict) and "temp" in obj["imperial"]:
        out["temp_f"] = float(obj["imperial"]["temp"])
    elif "temp" in obj:
        out["temp_f"] = float(obj["temp"])
    if "temp_f" not in out:
        return None
    # Humidity (%, or relative_humidity)
    if "humidity" in obj:
        out["humidity"] = int(float(obj["humidity"]))
    elif "relative_humidity" in obj:
        out["humidity"] = int(float(obj["relative_humidity"]))
    if "imperial" in obj and isinstance(obj["imperial"], dict) and "humidity" in obj["imperial"]:
        out["humidity"] = int(float(obj["imperial"]["humidity"]))
    # Pressure (baromin = inches of mercury)
    if "pressure" in obj:
        out["baromin"] = float(obj["pressure"])
    elif "baromin" in obj:
        out["baromin"] = float(obj["baromin"])
    elif "pressure_in" in obj:
        out["baromin"] = float(obj["pressure_in"])
    if "imperial" in obj and isinstance(obj["imperial"], dict) and "pressure" in obj["imperial"]:
        out["baromin"] = float(obj["imperial"]["pressure"])
    return out


def extract_observations_from_json(data: dict) -> Optional[Dict[str, Any]]:
    """Get current observation (temp_f, humidity, baromin) from embedded JSON."""
    if not data:
        return None
    # Current observation object
    for key in ["current_observation", "observation"]:
        if key in data and isinstance(data[key], dict):
            obs = _get_obs(data[key])
            if obs:
                return obs
    # First item in observations array (latest)
    if "observations" in data and isinstance(data["observations"], list) and data["observations"]:
        obs = _get_obs(data["observations"][0])
        if obs:
            return obs
    # Top-level imperial/metric
    if "imperial" in data and isinstance(data["imperial"], dict):
        obs = _get_obs(data["imperial"])
        if obs:
            return obs
    return _get_obs(data)


def extract_current_conditions(html: str) -> Dict[str, Any]:
    """
    Extract "Current Conditions" from the dashboard (shown when station is ONLINE).
    This is the live/latest reading, not the daily summary.
    """
    out: Dict[str, Any] = {}
    
    # Current temp: WU shows it as a big number near "Current Conditions" or at top
    # Patterns: "Current Conditions\n48" or just prominent temp display
    # Look for patterns like ">48<" or "48°F" near current/conditions
    
    # Pattern 1: number right after "Current Conditions" section
    m = re.search(r'Current\s*Conditions[^0-9]*?(\d+(?:\.\d+)?)\s*°?\s*F', html, re.IGNORECASE)
    if m and m.group(1):
        try:
            out["temp_f"] = float(m.group(1))
        except ValueError:
            pass
    
    # Pattern 2: look for temp in the main display area (often a large number)
    if "temp_f" not in out:
        # WU sometimes has the temp in a specific class or near "Feels Like"
        m = re.search(r'(\d+(?:\.\d+)?)\s*°\s*F[^<]*Feels\s*Like', html, re.IGNORECASE)
        if m and m.group(1):
            try:
                out["temp_f"] = float(m.group(1))
            except ValueError:
                pass
    
    # Pattern 3: look for temp value followed by °F in the conditions area
    if "temp_f" not in out:
        m = re.search(r'class="[^"]*temp[^"]*"[^>]*>\s*(\d+(?:\.\d+)?)\s*<', html, re.IGNORECASE)
        if m and m.group(1):
            try:
                out["temp_f"] = float(m.group(1))
            except ValueError:
                pass
    
    # Current humidity (near "HUMIDITY" label) — must be a real number like "90"
    m = re.search(r'HUMIDITY[^0-9]*(\d+(?:\.\d+)?)\s*%', html, re.IGNORECASE)
    if m and m.group(1):
        try:
            out["humidity"] = int(float(m.group(1)))
        except ValueError:
            pass
    
    # Current pressure (near "PRESSURE" label, in inches) — must be like "29.46"
    m = re.search(r'PRESSURE[^0-9]*(\d+\.\d+)\s*(?:in|")', html, re.IGNORECASE)
    if m and m.group(1):
        try:
            out["baromin"] = float(m.group(1))
        except ValueError:
            pass
    
    return out


def get_observations_from_source() -> Tuple[Dict[str, Any], str]:
    """
    Fetch station dashboard and return (observations_dict, source_description).
    Priority:
    1. Latest observation from observations array (most recent hourly reading)
    2. Current Conditions from HTML 
    3. Embedded JSON (current observation)
    4. Summary table (daily average — fallback when offline)
    """
    try:
        html = fetch_dashboard_html(SOURCE_URL)
    except Exception as e:
        return {}, f"fetch error: {e}"

    # First: try latest observation from the observations array (best for "right now")
    latest = extract_latest_observation(html)
    if latest.get("temp_f") is not None:
        return latest, "latest observation (ILONDO760 right now)"

    # Second: try Current Conditions HTML section
    current = extract_current_conditions(html)
    if current.get("temp_f") is not None:
        return current, "current conditions (ILONDO760 live)"

    # Third: try embedded JSON
    data = extract_json_from_page(html)
    obs = extract_observations_from_json(data)
    if obs and obs.get("temp_f") is not None:
        return obs, "current observation (ILONDO760 JSON)"

    # Fallback: summary table (daily stats from 760)
    summary = extract_summary_from_table(html)
    if summary.get("temp_f") is not None:
        return summary, "summary table (ILONDO760 daily average)"

    return {}, "no temp found in page"


def upload_to_wu(obs: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Upload to WU (same as curl GET). Sends tempf and any optional humidity/baromin.
    Returns (success, response_text).
    """
    temp_f = obs.get("temp_f")
    if temp_f is None:
        return False, "no temp_f in observations"
    params = {
        "ID": WU_STATION_ID,
        "PASSWORD": WU_STATION_KEY,
        "dateutc": "now",
        "tempf": f"{temp_f:.1f}",
        "action": "updateraw",
    }
    if "humidity" in obs and obs["humidity"] is not None:
        params["humidity"] = str(obs["humidity"])
    if "baromin" in obs and obs["baromin"] is not None:
        params["baromin"] = f"{obs['baromin']:.2f}"
    query = urllib.parse.urlencode(params)
    url_with_params = f"{WU_UPLOAD_URL}?{query}"
    try:
        with urllib.request.urlopen(url_with_params, timeout=10) as resp:
            body = resp.read().decode("utf-8").strip()
            return body == "success", body
    except Exception as e:
        return False, str(e)


def build_curl(obs: Dict[str, Any]) -> str:
    """Build the equivalent curl command for manual testing."""
    temp_f = obs.get("temp_f")
    if temp_f is None:
        return "(no temp)"
    params = {
        "ID": WU_STATION_ID,
        "PASSWORD": WU_STATION_KEY,
        "dateutc": "now",
        "tempf": f"{temp_f:.1f}",
        "action": "updateraw",
    }
    if obs.get("humidity") is not None:
        params["humidity"] = str(obs["humidity"])
    if obs.get("baromin") is not None:
        params["baromin"] = f"{obs['baromin']:.2f}"
    query = urllib.parse.urlencode(params)
    return f'curl -s "{WU_UPLOAD_URL}?{query}"'


def main():
    once = "--once" in sys.argv
    print("=" * 60)
    print("WU RELAY: ILONDO760 (source) → ILONDO983 (upload to)")
    print("=" * 60)
    print(f"Source:  {SOURCE_STATION} {SOURCE_URL}")
    print(f"Upload:  {WU_UPLOAD_URL} (station {WU_STATION_ID})")
    print(f"Interval: {RELAY_INTERVAL}s ({RELAY_INTERVAL // 60} min)" if not once else "Mode: single run")
    print("=" * 60)

    while True:
        obs, source = get_observations_from_source()
        temp_f = obs.get("temp_f")

        if temp_f is None:
            print(f"[{datetime.now():%H:%M:%S}] No temperature from source ({source}). Skipping.")
            time.sleep(RELAY_INTERVAL)
            continue

        success, response = upload_to_wu(obs)
        temp_c = (temp_f - 32) * 5 / 9
        extras = []
        if obs.get("humidity") is not None:
            extras.append(f"humidity={obs['humidity']}")
        if obs.get("baromin") is not None:
            extras.append(f"baromin={obs['baromin']}")
        extra_str = " " + " ".join(extras) if extras else ""

        if success:
            print(f"[{datetime.now():%H:%M:%S}] {temp_f:.1f}°F ({temp_c:.1f}°C){extra_str} from {source} → uploaded to ILONDO983 OK")
        else:
            print(f"[{datetime.now():%H:%M:%S}] {temp_f:.1f}°F → upload failed: {response}")

        if once:
            print(f"  curl: {build_curl(obs)}")
        print()

        if once:
            break
        time.sleep(RELAY_INTERVAL)


if __name__ == "__main__":
    main()
