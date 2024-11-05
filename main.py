# main.py
from light_sensor import LightSensor
from time import sleep, localtime
import ntptime
import wifi_config
from machine import Pin
import netman
import network

# Configuration Constants
SAMPLE_INTERVAL_SECONDS = 300   # Time between readings
TOTAL_RUNTIME_MINUTES = 840      # Total runtime
LED_WRITE_DELAY = 1           # Delay before LED flash after write, seconds
WIFI_CHECK_INTERVAL = 20      # Check WiFi every X readings

# Setup LED
led = Pin("LED", Pin.OUT)

def flash_led(times, duration=0.1):
    for _ in range(times):
        led.on()
        sleep(duration)
        led.off()
        sleep(duration)

def check_wifi_connection():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.isconnected():
        print("WiFi disconnected, attempting to reconnect...")
        try:
            netman.connectWiFi(wifi_config.WIFI_SSID, 
                             wifi_config.WIFI_PASSWORD, 
                             wifi_config.COUNTRY)
            print("WiFi reconnected!")
            try:
                ntptime.settime()  # Resync time
                print("Time resynced")
            except:
                print("Time resync failed")
            flash_led(3)  # 3 flashes for successful reconnection
            return True
        except:
            print("Reconnection failed")
            flash_led(2)  # 2 flashes for failed reconnection
            return False
    return True

# Setup sensors
sensor_1 = LightSensor(26)
sensor_2 = LightSensor(27)

def get_timestamp():
    year, month, day, hour, minute, second, _, _ = localtime()
    return f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

# Initial WiFi connection
print("Connecting to WiFi...")
try:
    netman.connectWiFi(wifi_config.WIFI_SSID, 
                      wifi_config.WIFI_PASSWORD, 
                      wifi_config.COUNTRY)
    flash_led(5)  # Flash 5 times on successful connection
    
    print("Syncing time...")
    ntptime.settime()
except Exception as e:
    print(f"Setup error: {e}")
    flash_led(2)  # Two flashes for error
    # Continue anyway - we can still log data

# Calculate total readings
total_readings = (TOTAL_RUNTIME_MINUTES * 60) // SAMPLE_INTERVAL_SECONDS
readings_taken = 0

print(f"Starting data collection for {TOTAL_RUNTIME_MINUTES} minutes...")
print(f"Taking readings every {SAMPLE_INTERVAL_SECONDS} seconds...")

with open('light_readings.csv', 'w') as file:
    # Write CSV header
    file.write('timestamp,sensor,raw_value,percentage,sensor,raw_value,percentage,raw_avg,pct_avg\n')
    
    while readings_taken < total_readings:
        try:
            # Periodically check WiFi
            if readings_taken % WIFI_CHECK_INTERVAL == 0:
                check_wifi_connection()
            
            # Get raw readings
            raw_1 = sensor_1.read()
            raw_2 = sensor_2.read()
            raw_avg = (raw_1 + raw_2) // 2
            
            # Get percentages
            pct_1 = sensor_1.read_percentage()
            pct_2 = sensor_2.read_percentage()
            avg_pct = round((pct_1 + pct_2) / 2, 1)
            
            timestamp = get_timestamp()
            
            # Save to file
            file.write(f'{timestamp},s1,{raw_1},{pct_1},s2,{raw_2},{pct_2},{raw_avg},{avg_pct}\n')
            file.flush()  # Ensure data is written to file
            
            # Print status
            print(f"Reading {readings_taken + 1}/{total_readings}: {timestamp} - Avg: {avg_pct}%")
            
            # Wait for LED_WRITE_DELAY before flashing
            sleep(LED_WRITE_DELAY)
            flash_led(1)  # Single flash for successful write
            
            readings_taken += 1
            
            # Calculate remaining sleep time after LED flash
            remaining_sleep = SAMPLE_INTERVAL_SECONDS - LED_WRITE_DELAY - 0.2  # 0.2 accounts for LED flash time
            if remaining_sleep > 0:
                sleep(remaining_sleep)
                
        except Exception as e:
            print(f"Error during reading: {e}")
            file.write(f'{get_timestamp()},ERROR,{str(e)}\n')
            file.flush()
            sleep(SAMPLE_INTERVAL_SECONDS)

print("Data collection complete!")
flash_led(3)  # Triple flash to indicate completion