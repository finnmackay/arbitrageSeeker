#!/usr/bin/env python3
"""
Raspberry Pi Weather Station Upload Script
Reads DS18B20 temperature sensor and uploads to Weather Underground
"""
import requests
import time
from datetime import datetime

# Weather Underground credentials
WU_STATION_ID = "ILONDO983"
WU_STATION_KEY = "CPBgPEJX"
WU_UPLOAD_URL = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php"

# Upload interval (seconds)
UPLOAD_INTERVAL = 300  # 5 minutes

# Sensor setup
try:
    from w1thermsensor import W1ThermSensor
    sensor = W1ThermSensor()
    SENSOR_AVAILABLE = True
except Exception as e:
    print(f"Sensor not available: {e}")
    SENSOR_AVAILABLE = False


def read_temperature_c():
    """Read temperature from DS18B20 sensor in Celsius"""
    if not SENSOR_AVAILABLE:
        return None
    try:
        return sensor.get_temperature()
    except Exception as e:
        print(f"Sensor read error: {e}")
        return None


def celsius_to_fahrenheit(temp_c):
    """Convert Celsius to Fahrenheit (WU API requires F)"""
    return (temp_c * 9/5) + 32


def upload_to_wu(temp_c):
    """Upload temperature to Weather Underground"""
    temp_f = celsius_to_fahrenheit(temp_c)

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
        print(f"Upload error: {e}")
        return False


def main():
    """Main loop - read sensor and upload every 5 minutes"""
    print("=" * 40)
    print("RASPBERRY PI WEATHER STATION")
    print(f"Station ID: {WU_STATION_ID}")
    print(f"Upload interval: {UPLOAD_INTERVAL} seconds")
    print("=" * 40)

    if not SENSOR_AVAILABLE:
        print("ERROR: No sensor detected. Check wiring.")
        return

    while True:
        temp_c = read_temperature_c()

        if temp_c is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if upload_to_wu(temp_c):
                print(f"[{timestamp}] Uploaded: {temp_c:.1f}°C ({celsius_to_fahrenheit(temp_c):.1f}°F)")
            else:
                print(f"[{timestamp}] Upload failed: {temp_c:.1f}°C")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to read sensor")

        time.sleep(UPLOAD_INTERVAL)


if __name__ == "__main__":
    main()
