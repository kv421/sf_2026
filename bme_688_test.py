import bme680
import time

def run_example():
    print("Initializing BME688 Sensor...")

    try:
        # Try to connect to the sensor. 
        # SparkFun defaults to 0x77, but some boards use 0x76.
        try:
            sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY) # 0x76
        except (RuntimeError, IOError):
            sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY) # 0x77

        print("Sensor found!")

        # These oversampling settings help reduce noise
        sensor.set_humidity_oversample(bme680.OS_2X)
        sensor.set_pressure_oversample(bme680.OS_4X)
        sensor.set_temperature_oversample(bme680.OS_8X)
        sensor.set_filter(bme680.FILTER_SIZE_3)

        # Enable gas metering
        sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        sensor.set_gas_heater_temperature(320)
        sensor.set_gas_heater_duration(150)
        sensor.select_gas_heater_profile(0)

        print("\nReading data... (Press CTRL+C to quit)")
        print("-" * 40)

        while True:
            if sensor.get_sensor_data():
                output = "{0:.2f} C, {1:.2f} %RH, {2:.2f} hPa".format(
                    sensor.data.temperature,
                    sensor.data.humidity,
                    sensor.data.pressure)

                # The gas sensor takes a moment to warm up; it may show unstable readings initially
                if sensor.data.heat_stable:
                    print(f"{output}, Gas: {sensor.data.gas_resistance} Ohms")
                else:
                    print(f"{output}, Gas: (Heating...)")

            time.sleep(1)

    except Exception as e:
        print(f"\nError connecting to sensor: {e}")
        print("Troubleshooting tips:")
        print("1. Check wiring (SDA/SCL swapped?)")
        print("2. Run 'i2cdetect -y 1' to verify the Pi sees the device.")

if __name__ == '__main__':
    run_example()