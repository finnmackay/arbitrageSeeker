#!/usr/bin/env python3
"""
Computer Receiver - receives from Pi, logs locally, uploads to WU
Run on your Mac: python3 computer_receiver.py
"""
from flask import Flask, request, jsonify
import requests
from datetime import datetime
import json
import os

app = Flask(__name__)

# Weather Underground
WU_STATION_ID = "ILONDO983"
WU_STATION_KEY = "CPBgPEJX"
WU_UPLOAD_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

# Local log file
LOG_FILE = "temperature_log.jsonl"

# Store readings for averaging
readings = []


def log_reading(temp_c, timestamp):
    """Log reading to local file"""
    entry = {
        "temp_c": temp_c,
        "timestamp": timestamp,
        "logged_at": datetime.utcnow().isoformat()
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def upload_to_wu(temp_c):
    """Upload to Weather Underground"""
    temp_f = (temp_c * 9/5) + 32
    params = {
        "ID": WU_STATION_ID,
        "PASSWORD": WU_STATION_KEY,
        "dateutc": "now",
        "tempf": f"{temp_f:.1f}",
        "action": "updateraw"
    }
    try:
        response = requests.get(WU_UPLOAD_URL, params=params, timeout=10)
        return response.text.strip() == "success"
    except Exception as e:
        print(f"WU upload error: {e}")
        return False


@app.route("/temperature", methods=["POST"])
def receive_temperature():
    """Receive temperature from Pi"""
    data = request.json
    temp_c = data.get("temp_c")
    timestamp = data.get("timestamp")

    if temp_c is None:
        return jsonify({"error": "No temperature"}), 400

    # Log locally
    log_reading(temp_c, timestamp)

    # Store for averaging
    readings.append({"temp": temp_c, "time": datetime.utcnow()})

    # Keep only last 5 minutes of readings
    cutoff = datetime.utcnow().timestamp() - 300
    readings[:] = [r for r in readings if r["time"].timestamp() > cutoff]

    # Calculate average
    avg_temp = sum(r["temp"] for r in readings) / len(readings)

    # Upload to WU
    if upload_to_wu(avg_temp):
        print(f"[{datetime.now():%H:%M:%S}] Received: {temp_c:.1f}°C | Avg: {avg_temp:.1f}°C | Uploaded to WU")
        return jsonify({"status": "ok", "uploaded": True, "avg_temp": avg_temp})
    else:
        print(f"[{datetime.now():%H:%M:%S}] Received: {temp_c:.1f}°C | WU upload failed")
        return jsonify({"status": "ok", "uploaded": False})


@app.route("/readings", methods=["GET"])
def get_readings():
    """View recent readings"""
    return jsonify({
        "count": len(readings),
        "readings": [{"temp": r["temp"], "time": r["time"].isoformat()} for r in readings[-10:]]
    })


@app.route("/", methods=["GET"])
def index():
    """Status page"""
    return f"""
    <h1>Weather Station Receiver</h1>
    <p>Station: {WU_STATION_ID}</p>
    <p>Readings buffered: {len(readings)}</p>
    <p>Log file: {LOG_FILE}</p>
    <p><a href="/readings">View recent readings</a></p>
    """


if __name__ == "__main__":
    print("=" * 40)
    print("WEATHER STATION RECEIVER")
    print(f"Station: {WU_STATION_ID}")
    print(f"Log file: {LOG_FILE}")
    print("=" * 40)
    print("Waiting for Pi data on port 5050...")
    app.run(host="0.0.0.0", port=5050)
