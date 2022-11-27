# Show temperature and humidity from BLE ADV 'ATC MiThermometer'
Show telemetry data from Bluetooth BLE advertising device type of 'ATC_MiThermometer'

Show telemetry data (PVVX) after apply custom firmware https://github.com/pvvx/ATC_MiThermometer (fork https://github.com/atc1441/ATC_MiThermometer) for the Xiaomi Thermometer LYWSD03MMC.

Used Python module : Bleak - https://bleak.readthedocs.io

```
pip install bleak
python3 -i BLE_ADV_ATC_MiThermometer.py
```

Result:

![image](https://user-images.githubusercontent.com/3278842/204113485-b3d1c3a7-5936-4b89-8564-f27fd5e50d1f.png)


Telemetry data of custom PVVX format (https://github.com/pvvx/ATC_MiThermometer):

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
