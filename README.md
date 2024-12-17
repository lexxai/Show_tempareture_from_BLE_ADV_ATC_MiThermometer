# Show temperature and humidity from BLE ADV 'ATC MiThermometer'

This project shows telemetry data from a Bluetooth BLE advertising device of type 'ATC_MiThermometer'. It decodes telemetry data (PVVX) after applying custom firmware from [pvvx/ATC_MiThermometer](https://github.com/pvvx/ATC_MiThermometer) (forked from [atc1441/ATC_MiThermometer](https://github.com/atc1441/ATC_MiThermometer)) for the Xiaomi Thermometer LYWSD03MMC.

## New Features (Version 0.2.0):
- **Refactored Code to Use Classes**: The original code (version 0.1.0) has been rewritten to use object-oriented programming (OOP) principles, leveraging classes for better structure and maintainability.
- **Async Support with `asyncio`**: Major parts of the code have been refactored to use asynchronous programming with `asyncio` to improve performance, especially for handling I/O-bound tasks.
- **Alarm System**: Added an alarm system with configurable low and high temperature thresholds. Alerts are triggered when the temperature exceeds or drops below these thresholds.
- **Notification Modules**: Integrated a set of notification modules to notify users about alarm events. The notification system supports various output methods, including console, logging, and Discord messages.
- **Design Patterns for Notifications**: Used design patterns to define multiple methods for notifications and outputs, making the system more flexible and extensible.
- **Async Output via Queue Tasks**: Output modules now support asynchronous processing using queue tasks, enabling more efficient handling of data.
- **Logger Synchronization**: The logger module uses queue tasks for async output and is synchronized with the output module using a `Lock` to ensure async safe operations.
- **Configurable Parameters via Console**: Added parameters that can be controlled via the command line when running the console application. Common settings can now be read from the environment or from an `.env` file, making the configuration process more flexible and environment-specific.
- **Windows `.exe` Build**: Present scripts are included for building a Windows `.exe` version of the application, making it easier to run the tool natively on Windows OS without needing a Python environment.
- **Poetry for Package Management**: The project uses [Poetry](https://python-poetry.org/) for dependency management and packaging, ensuring consistent environments across development and production setups.


This is a very simple script for decoding telemetry from Bluetooth advertising thermometer data.

**Used Python Module**: [Bleak](https://bleak.readthedocs.io)


## Run MiTermometerPVVX

To run the application, first install the dependencies (excluding development dependencies) using Poetry:

```bash
poetry install --without dev
```

Then, you can run the application with the following command:

```bash
poetry run python MiTermometerPVVX
```
This will start the application, which will decode and display telemetry data from the ATC MiThermometer.

## Build `.exe`

To build a Windows `.exe` version of the application, follow these steps:

1. **Install dependencies (including development dependencies)** with Poetry:

    ```bash
    poetry install --with dev
    ```

2. **Navigate to the `script` directory**:

    ```bash
    cd script
    ```

3. **Run the `build.cmd` script** to generate the `.exe` file:

    ```bash
    build.cmd
    ```

4. After the build process completes, you will find the `.exe` file in the `pyinstall\dist\` directory, named `MiTermometerPVVX.exe`.

This `.exe` file can be run on a Windows system without needing a Python environment installed. It includes all dependencies bundled into the executable.


## Result of MiTermometerPVVX:

<img width="848" alt="With notification" src="https://github.com/user-attachments/assets/37227932-240d-40d5-8f85-3c67d7085183" />



## Parameter of app
```
usage: MiTermometerPVVX [-h] [-n NAMES [NAMES ...]] [-lt ALERT_LOW_THRESHOLD] [-ht ALERT_HIGH_THRESHOLD] [-st SENT_THRESHOLD_TEMP] [-dtp]
                        [-m {auto,passive,active}] [-nt {logger,discord,none} [{logger,discord,none} ...]] [-d]

Show temperature and humidity from BLE ADV 'ATC MiThermometer' and alarm on temperature.

options:
  -h, --help            show this help message and exit
  -n NAMES [NAMES ...], --names NAMES [NAMES ...]
                        Define custom names in the format KEY=VALUE, where KEY can match with end of device name (e.g., 12345="OUTSIDE"). Default is
                        not used.
  -lt ALERT_LOW_THRESHOLD, --alert-low-threshold ALERT_LOW_THRESHOLD
                        Set the temperature alert threshold less than (e.g., 5.0 for 5°C). Use 'None' to disable. Default is 8.0.
  -ht ALERT_HIGH_THRESHOLD, --alert-high-threshold ALERT_HIGH_THRESHOLD
                        Set the temperature alert threshold higher than (e.g., 40.0 for 40°C). Use 'None' to disable. Default is 36.0.
  -st SENT_THRESHOLD_TEMP, --sent_threshold_temp SENT_THRESHOLD_TEMP
                        Set the delta temperature alert threshold for send next notification. Default is 2.0.
  -dtp, --disable_text_pos
                        Used when need to disable use text position and use plain print. Default is enabled.
  -m {auto,passive,active}, --mode {auto,passive,active}
                        Select scan mode. Default is 'auto'.
  -nt {logger,discord,none} [{logger,discord,none} ...], --notification {logger,discord,none} [{logger,discord,none} ...]
                        Select notification mode individually or multiple, separated by space. Default is 'logger'.
  -d, --debug           Enable debug output. Default is disabled.
```

## Exaple of .env file with setings:
```
DEBUG=False

NAME_5EDB77="OUTSIDE ROOM"
NAME_F6ED7A="MAIN ROOM"

ALERT_LOW_THRESHOLD=6.0
ALERT_HIGH_THRESHOLD=36.0
SENT_THRESHOLD_TEMP=3.0

# Coma separated list
# NOTIFICATION=logger,discord
NOTIFICATION=logger

# auto, passive, active
BLE_SCANNER_MODE=passive

DISCORD_WEB_HOOKS=https://discord.com/api/webhooks/.....
```

## Telemetry data of custom PVVX format (https://github.com/pvvx/ATC_MiThermometer):

Custom format (all data little-endian):

UUID 0x181A - size 19: Custom extended format in 0.01 units (all data little-endian):

```
uint8_t     MAC[6]; // [0] - lo, .. [6] - hi digits
int16_t     temperature;    // x 0.01 degree
uint16_t    humidity;       // x 0.01 %
uint16_t    battery_mv;     // mV
uint8_t     battery_level;  // 0..100 %
uint8_t     counter;        // measurement count
uint8_t     flags;  // GPIO_TRG pin (marking "reset" on circuit board) flags: 
                    // bit0: Reed Switch, input
                    // bit1: GPIO_TRG pin output value (pull Up/Down)
                    // bit2: Output GPIO_TRG pin is controlled according to the set parameters
                    // bit3: Temperature trigger event
                    // bit4: Humidity trigger event
```

Python code:
```
temp=int.from_bytes(advatc[6:8], byteorder='little', signed=True)/100.0
humidity=int.from_bytes(advatc[8:10], byteorder='little', signed=True)/100.0
batteryv=int.from_bytes(advatc[10:12], byteorder='little', signed=False)
battery=int.from_bytes(advatc[12:13], byteorder='little', signed=False)    
count=int.from_bytes(advatc[13:14], byteorder='little', signed=False) 
flag=int.from_bytes(advatc[14:15], byteorder='little', signed=False) 
```
