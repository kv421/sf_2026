import time
import sys
import os
import csv
from datetime import datetime
import board
import adafruit_dht
import adafruit_sgp40
import bme680
import boto3

# Add path for DFRobot sensor (replicating existing script logic)
# This looks for libraries 3 directories up from this script
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

try:
    from DFRobot_MultiGasSensor import *
except ImportError:
    print("Warning: Could not import DFRobot_MultiGasSensor. NH3 data will be missing.")
    DFRobot_MultiGasSensor_UART = None

# Config
BUCKET_NAME = "sf20261"
PROFILE_NAME = "s3-access"
DATA_DIR = "data"
UPLOAD_INTERVAL_SEC = 5 

# Ensure data dir exists
os.makedirs(DATA_DIR, exist_ok=True)

# S3 Setup
try:
    session = boto3.Session(profile_name=PROFILE_NAME)
    s3 = session.client('s3')
except Exception as e:
    print(f"Error setting up AWS Session: {e}")
    sys.exit(1)

def setup_sensors():
    sensors = {}
    
    # 1. DHT22
    try:
        # Use existing logic from dht22Test.py
        sensors['dht'] = adafruit_dht.DHT22(board.D6)
    except Exception as e:
        print(f"Error Init DHT22: {e}")
        sensors['dht'] = None

    # 2. SGP40
    try:
        # Use existing logic from sgp40Test.py
        i2c = board.I2C()
        sensors['sgp'] = adafruit_sgp40.SGP40(i2c)
    except Exception as e:
        print(f"Error Init SGP40: {e}")
        sensors['sgp'] = None

    # 3. BME688
    try:
        # Use existing logic from bme_688_test.py
        try:
            bme = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
        except (RuntimeError, IOError):
            bme = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
            
        bme.set_humidity_oversample(bme680.OS_2X)
        bme.set_pressure_oversample(bme680.OS_4X)
        bme.set_temperature_oversample(bme680.OS_8X)
        bme.set_filter(bme680.FILTER_SIZE_3)
        bme.set_gas_status(bme680.ENABLE_GAS_MEAS)
        bme.set_gas_heater_temperature(320)
        bme.set_gas_heater_duration(150)
        bme.select_gas_heater_profile(0)
        sensors['bme'] = bme
    except Exception as e:
        print(f"Error Init BME688: {e}")
        sensors['bme'] = None

    # 4. DFRobot NH3
    try:
        if DFRobot_MultiGasSensor_UART:
            # Use existing logic from sensorCollectionScript.py
            gas = DFRobot_MultiGasSensor_UART(9600)
            
            print("Initializing NH3 sensor (waiting for mode change)...")
            # Retry logic for mode change
            attempts = 0
            mode_changed = False
            while attempts < 5:
                if gas.change_acquire_mode(gas.NH3):
                    mode_changed = True
                    break
                time.sleep(1)
                attempts += 1
            
            if mode_changed:
                gas.set_temp_compensation(gas.ON)
                sensors['nh3'] = gas
                print("NH3 Init Success")
            else:
                print("NH3 Init Failed (Mode change timeout)")
                sensors['nh3'] = None
        else:
            sensors['nh3'] = None
    except Exception as e:
        print(f"Error Init NH3: {e}")
        sensors['nh3'] = None
        
    return sensors

def read_dht(dht):
    if not dht: return None, None
    try:
        return dht.temperature, dht.humidity
    except RuntimeError:
        # DHT often fails to read, return None to skip this reading
        return None, None 

def read_sgp(sgp, temp=25, hum=50):
    if not sgp: return None
    try:
        return sgp.measure_index(temp, hum)
    except Exception:
        return None

def read_bme(bme):
    if not bme: return None, None, None, None
    try:
        if bme.get_sensor_data():
            temp = bme.data.temperature
            hum = bme.data.humidity
            pres = bme.data.pressure
            gas = bme.data.gas_resistance if bme.data.heat_stable else None
            return temp, hum, pres, gas
    except Exception:
        pass
    return None, None, None, None

def read_nh3(nh3):
    if not nh3: return None
    try:
        return nh3.read_gas_concentration()
    except Exception:
        return None

def main():
    print(f"Starting Sensor Monitor. Bucket: {BUCKET_NAME}")
    sensors = setup_sensors()
    
    while True:
        try:
            timestamp = datetime.now().isoformat()
            
            # Read BME first
            b_temp, b_hum, b_pres, b_gas = read_bme(sensors['bme'])
            
            # Read DHT
            d_temp, d_hum = read_dht(sensors['dht'])
            
            # Determine compensation values for SGP
            comp_temp = b_temp if b_temp is not None else (d_temp if d_temp is not None else 25)
            comp_hum = b_hum if b_hum is not None else (d_hum if d_hum is not None else 50)
            
            # Read SGP
            s_voc = read_sgp(sensors['sgp'], comp_temp, comp_hum)
            
            # Read NH3
            n_conc = read_nh3(sensors['nh3'])
            
            # Prepare row
            row = [timestamp, b_temp, b_hum, b_pres, b_gas, d_temp, d_hum, s_voc, n_conc]
            print(f"Read: {row}")
            
            # File Management
            today = datetime.now().strftime("%Y-%m-%d")
            filename = os.path.join(DATA_DIR, f"sensor_data_{today}.csv")
            file_exists = os.path.isfile(filename)
            
            with open(filename, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['Timestamp', 'BME_Temp', 'BME_Hum', 'BME_Pres', 'BME_Gas_Ohms', 'DHT_Temp', 'DHT_Hum', 'SGP_VOC', 'NH3_Conc'])
                writer.writerow(row)
            
            # Upload to S3
            s3_key = f"sensor_data/{today}.csv"
            try:
                s3.upload_file(filename, BUCKET_NAME, s3_key)
                print(f"Uploaded to s3://{BUCKET_NAME}/{s3_key}")
            except Exception as e:
                print(f"S3 Upload failed: {e}")
                
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("Stopping...")
            break
        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
