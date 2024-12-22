# Show temperature and humidity from BLE ADV 'ATC MiThermometer'

This project shows telemetry data from a Bluetooth BLE advertising device of type 'ATC_MiThermometer'. It decodes telemetry data (PVVX) after applying custom firmware from [pvvx/ATC_MiThermometer](https://github.com/pvvx/ATC_MiThermometer) (forked from [atc1441/ATC_MiThermometer](https://github.com/atc1441/ATC_MiThermometer)) for the Xiaomi Thermometer LYWSD03MMC.

<img src="https://user-images.githubusercontent.com/3278842/204167827-ad60ba14-c568-4914-939f-60d522297c80.png" width="150" height="150">
## New Features (Version 0.3.1):

- **Refactored Code to Use Classes**: The original code (version 0.1.0) has been rewritten to use object-oriented programming (OOP) principles, leveraging classes for better structure and maintainability.
- **Async Support with `asyncio`**: Major parts of the code have been refactored to use asynchronous programming with `asyncio` to improve performance, especially for handling I/O-bound tasks.
- **Alarm System**: Added an alarm system with configurable low and high temperature thresholds. Alerts are triggered when the temperature exceeds or drops below these thresholds.
- **Notification Modules**: Integrated a set of notification modules to notify users about alarm events. The notification system supports various output methods, including console, logging, and Discord messages.
- **Multi-Platform Notifications**: Added support for platform-specific notification systems:
  - **Windows**: Uses `windows-toasts` for native notifications with history support via `winrt-Windows.UI.Notifications`.
  - **macOS**: Uses `pync`, a wrapper for `terminal-notifier`, to provide basic notification functionality.
  - **Linux**: Integrates the `plyer` package for notifications (not yet fully tested).
- **Design Patterns for Notifications**: Used design patterns to define multiple methods for notifications and outputs, making the system more flexible and extensible.
- **Async Output via Queue Tasks**: Output modules now support asynchronous processing using queue tasks, enabling more efficient handling of data.
- **Logger Synchronization**: The logger module uses queue tasks for async output and is synchronized with the output module using a `Lock` to ensure async-safe operations.
- **Configurable Parameters via Console**: Added parameters that can be controlled via the command line when running the console application. Common settings can now be read from the environment or from an `.env` file, making the configuration process more flexible and environment-specific.
- **Windows and macOS `.exe` Build**: Present scripts are included for building a `.exe` version of the application. The build process has been tested on both Windows and macOS, making it easier to run the tool natively on these platforms without needing a Python environment.
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

To build a `.exe` version of the application for Windows or macOS, follow these steps:

1. **Install dependencies (including development dependencies)** with Poetry:

    ```bash
    poetry install --with dev
    ```

2. **Navigate to the `script` directory**:

    ```bash
    cd script
    ```

3. **Run the appropriate build script** based on your operating system:

   - For **Windows**, run:

     ```bash
     build.cmd
     ```

   - For **macOS**, run:

     ```bash
     build.sh
     ```

4. After the build process completes, the `.exe` file will be located in the `pyinstall\dist\` directory:

   - For **Windows**, the file will be named `MiTermometerPVVX.exe`.
   - For **macOS**, the file will be named `MiTermometerPVVX`.

These `.exe` files can be run natively on their respective systems without needing a Python environment. All dependencies are bundled into the executable.


## Use .env file for settings of applications

By defualt, the application will use system environment variables to set parameters.
If need override system environment variables, please create a `.env` file in the script directory or parent directory. 

Executable file not contain inside any data from .env file.

If use executable, please put .env file in the same directory as the executable or directory of executable file located. If .env file was successfully loaded on console is message "Loaded .env file". 

### Settings of .env file:
**NAME_{KEY}** - Define custom names of devices in the format KEY=VALUE, where KEY can match with end of device name (e.g., 12345="OUTSIDE").

**ALERT_LOW_THRESHOLD** - Define the low threshold for temperature alerts. Settings for all devices.

**ALERT_HIGH_THRESHOLD** - Define the high threshold for temperature alerts. Settings for all devices.

**SENT_THRESHOLD_TEMP** - Define the temperature threshold for sending next notifications. Next notification will be sent when absoulte value of temperature changed more than this value.

**NOTIFICATION** - Define the notification mode. Values separated by comma. Values: logger, discord, system, none. Can be combined.

**DISCORD_WEB_HOOKS** - Define the Discord webhook URL for sending notifications if use discord as notification mode. More on section about Discord Notifications.

 
**BLE_SCANNER_MODE** - Define the BLE scanner mode. Values: auto, passive, active. Please read Note section.


### Exaple of .env file with setings:
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
DISCORD_WEB_HOOKS=https://discord.com/api/webhooks/.....

# auto, passive, active
BLE_SCANNER_MODE=passive
```


## Notes

- **Passive Mode**: This application works by grabbing advertising messages from Bluetooth Low Energy (BLE) devices in passive mode. In passive mode, no bidirectional communication is required with the devices to obtain telemetry data. This means that the application can retrieve data without draining the power of the BLE devices.

- **Active Mode**: In active mode, communication with the BLE devices is required to fetch telemetry data, which can drain the power elements of the devices. 

- **Platform-Specific Behavior**: The application has been tested to work on both macOS and Windows. However, due to architectural limitations on macOS, it **cannot** run the scanner in passive mode. Only active mode will work on macOS, so **be cautious** when running the application on this platform.


## Result of MiTermometerPVVX:

<img width="848" alt="With notification" src="https://github.com/user-attachments/assets/37227932-240d-40d5-8f85-3c67d7085183" />



## Parameter of app
```
usage: MiTermometerPVVX.exe [-h] [-n NAMES [NAMES ...]] [-lt ALERT_LOW_THRESHOLD] [-ht ALERT_HIGH_THRESHOLD] [-st SENT_THRESHOLD_TEMP] [-dtp] [-m {auto,passive,active}]
                            [-nf {logger,discord,system,none} [{logger,discord,system,none} ...]] [-d] [-v]

Show temperature and humidity from BLE ADV 'ATC MiThermometer' and alarm on temperature.

options:
  -h, --help            show this help message and exit
  -n NAMES [NAMES ...], --names NAMES [NAMES ...]
                        Define custom names in the format KEY=VALUE, where KEY can match with end of device name (e.g., 12345="OUTSIDE"). Default is not used.
  -lt ALERT_LOW_THRESHOLD, --alert-low-threshold ALERT_LOW_THRESHOLD
                        Set the temperature alert threshold less than (e.g., 5.0 for 5°C). Use 'None' to disable. Default is None.
  -ht ALERT_HIGH_THRESHOLD, --alert-high-threshold ALERT_HIGH_THRESHOLD
                        Set the temperature alert threshold higher than (e.g., 40.0 for 40°C). Use 'None' to disable. Default is None.
  -st SENT_THRESHOLD_TEMP, --sent_threshold_temp SENT_THRESHOLD_TEMP
                        Set the delta temperature alert threshold for send next notification. Default is 1.0.
  -dtp, --disable_text_pos
                        Used when need to disable use text position and use plain print. Default is enabled.
  -m {auto,passive,active}, --mode {auto,passive,active}
                        Select scan mode. Default is 'auto'.
  -nf {logger,discord,system,none} [{logger,discord,system,none} ...], --notification {logger,discord,system,none} [{logger,discord,system,none} ...]
                        Select notification mode individually or multiple, separated by space. Default is 'logger'.
  -d, --debug           Enable debug output. Default is disabled.
  -v, --version         Show the version of the application
```


## System Notification

### Windows OS

For native Windows systems, the application uses the `windows-toasts` package, which leverages the native Windows UI via `winrt-Windows.UI.Notifications`. This allows for advanced features, such as maintaining a notification history, whereas simple notifications typically display messages for a short duration.

**Example usage:**

![Example Notification 1](https://github.com/user-attachments/assets/d5614a13-9ca6-4a22-ba01-5019249710e0)

![Example Notification 2](https://github.com/user-attachments/assets/562ecbb0-621c-4a71-84f5-0c2e3542117e)


### macOS

On macOS, the application uses the `pync` package, a wrapper for the `terminal-notifier` console application. This provides basic notification functionality in macOS. History of all notifiactions present.

**Example usage:**

<img width="759" alt="Example Notification 1" src="https://github.com/user-attachments/assets/f9c53181-d8e7-4ed9-953e-49366545e30a" />

<img width="769" alt="Example Notification 2" src="https://github.com/user-attachments/assets/807c8e08-5f68-4b09-b59e-f1c679491846" />


### Linux

For Linux, the application utilizes the `plyer` package for notifications. However, this implementation has not yet been tested and may require further validation.

## Dicord Notification

Information about alarm can be sent also to Discord channel.
To begin using the application discord notifications, you need to obtain a Webhook URL.

Values can get on Dicsord cabinet of user's channel settings : Channel Settings -> Integration -> Webhook -> New Webhook.

For more information: [Discord Webhooks](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).

### Example of Notification:

<img width="478" alt="dicord notification" src="https://github.com/user-attachments/assets/03d02751-4190-4e99-82e8-5b62f54652d3" />




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
