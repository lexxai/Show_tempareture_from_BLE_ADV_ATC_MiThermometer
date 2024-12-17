# Show temperature and humidity from BLE ADV 'ATC MiThermometer'
Show telemetry data from Bluetooth BLE advertising device type of 'ATC_MiThermometer'

Show telemetry data (PVVX) after apply custom firmware https://github.com/pvvx/ATC_MiThermometer (fork https://github.com/atc1441/ATC_MiThermometer) for the Xiaomi Thermometer LYWSD03MMC.

<img src="https://user-images.githubusercontent.com/3278842/204167827-ad60ba14-c568-4914-939f-60d522297c80.png" width="150" height="150">


This is a very simple script for decoding telemetry from bluetooth advertising thermometer data.

Used python module : Bleak - https://bleak.readthedocs.io

## Run MiTermometerPVVX

```
poetry install --without dev
poetry run python MiTermometerPVVX
```

## Build .exe
```
poetry install --with dev
cd script
build.cmd
```
exe file placed on `pyinstall\dist\MiTermometerPVVX.exe`

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
SENT_TRGESHOLD_TEMP=1.0

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
