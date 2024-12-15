# Show temperature and humidity from BLE ADV 'ATC MiThermometer'
Show telemetry data from Bluetooth BLE advertising device type of 'ATC_MiThermometer'

Show telemetry data (PVVX) after apply custom firmware https://github.com/pvvx/ATC_MiThermometer (fork https://github.com/atc1441/ATC_MiThermometer) for the Xiaomi Thermometer LYWSD03MMC.

<img src="https://user-images.githubusercontent.com/3278842/204167827-ad60ba14-c568-4914-939f-60d522297c80.png" width="150" height="150">


This is a very simple script for decoding telemetry from bluetooth advertising thermometer data.

Used python module : Bleak - https://bleak.readthedocs.io

## Run MiTermometerPVVX

```
pip install bleak
python3 MiTermometerPVVX/main.py
```

## Build .exe
```
pip install pyinstaller 
script\build.cmd
```
exe file placed on pyinstall\dist\MiTermometerPVVX.exe

## Result of MiTermometerPVVX:

![image](https://user-images.githubusercontent.com/3278842/204151276-c43508b4-945a-4859-8740-efbf5d425674.png)

![Screenshot 2023-06-07 144630](https://github.com/lexxai/Show_temperature_from_BLE_ADV_ATC_MiThermometer/assets/3278842/78d6317c-18ca-41ad-9909-af9819620099)

<img width="710" alt="With notification" src="https://github.com/user-attachments/assets/0a3079a6-32dc-4f43-9cdc-b09846088e53" />




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
