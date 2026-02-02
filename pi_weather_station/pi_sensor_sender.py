#!/usr/bin/env python3
"""
Pi Sensor - sends temperature to your computer
"""
import requests
import time
from datetime import datetime

# Your computer's IP (find with: ipconfig getifaddr en0)
COMPUTER_IP = "192.168.1.100"  # <-- CHANGE THIS
COMPUTER_PORT = 5050

SEND_INTERVAL = 60  # Send every 1 minute

try:
    from w1thermsensor import W1ThermSensor
    sensor = W1ThermSensor()
except:
    sensor = None
    print("No sensor - running in test mode")


def read_temp():
    if sensor:
        return sensor.get_temperature()
    return None


def send_to_computer(temp_c):
    try:
        url = f"http://{COMPUTER_IP}:{COMPUTER_PORT}/temperature"
        data = {
            "temp_c": temp_c,
            "timestamp": datetime.utcnow().isoformat(),
            "station": "ILONDO983"
        }
        response = requests.post(url, json=data, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Send error: {e}")
        return False


if __name__ == "__main__":
    print(f"Sending to {COMPUTER_IP}:{COMPUTER_PORT}")

    while True:
        temp = read_temp()
        if temp:
            if send_to_computer(temp):
                print(f"[{datetime.now():%H:%M:%S}] Sent: {temp:.1f}°C")
            else:
                print(f"[{datetime.now():%H:%M:%S}] Failed to send")
        time.sleep(SEND_INTERVAL)
