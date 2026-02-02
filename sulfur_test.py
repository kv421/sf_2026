import bme680
import time

# --- CALIBRATION SETTINGS ---
# You must adjust these numbers based on your environment!
CLEAN_AIR_OHMS = 50000  # Resistance in fresh air (Goal: Higher is cleaner)
BAD_AIR_OHMS = 1000     # Resistance in sulfur-heavy air (Goal: Lower is dirtier)

def get_sulfur_intensity(current_ohms):
    """
    Converts resistance to a 0-100% intensity scale.
    """
    # 1. Clamp the value between our min and max
    if current_ohms > CLEAN_AIR_OHMS: current_ohms = CLEAN_AIR_OHMS
    if current_ohms < BAD_AIR_OHMS: current_ohms = BAD_AIR_OHMS

    # 2. Map the value to 0-100 range (Inverted logic: Lower Ohms = Higher %)
    # Formula: (Max - Current) / (Max - Min) * 100
    intensity = (CLEAN_AIR_OHMS - current_ohms) / (CLEAN_AIR_OHMS - BAD_AIR_OHMS) * 100
    return intensity

try:
    print("Initializing Sensor...")
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    # Set up sensor for gas detection
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)

    print("Warming up... (Readings will stabilize in ~5 mins)")

    while True:
        if sensor.get_sensor_data():
            if sensor.data.heat_stable:
                ohms = sensor.data.gas_resistance
                sulfur_level = get_sulfur_intensity(ohms)
                
                # Create a visual bar for the terminal
                bar_length = int(sulfur_level / 5) # 20 chars max
                visual_bar = "█" * bar_length + "-" * (20 - bar_length)

                print(f"Resistance: {ohms:.0f} Ohms | Sulfur Intensity: {sulfur_level:.1f}% | [{visual_bar}]")
            else:
                print("Heating...")
        
        time.sleep(1)

except KeyboardInterrupt:
    print("\nExited.")