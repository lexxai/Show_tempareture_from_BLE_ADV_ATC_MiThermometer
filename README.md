# Show temperature and humidity from BLE ADV 'ATC MiThermometer'
Show telemetry data from Bluetooth BLE advertising device type of 'ATC_MiThermometer'

Show telemetry data after apply custom firmware https://github.com/pvvx/ATC_MiThermometer (fork https://github.com/atc1441/ATC_MiThermometer) for the Xiaomi Thermometer LYWSD03MMC.

Used Python module : Bleak - https://bleak.readthedocs.io

```
pip install bleak
python3 -i BLE_ADV_ATC_MiThermometer.py
```

Result:

![image](https://user-images.githubusercontent.com/3278842/204113485-b3d1c3a7-5936-4b89-8564-f27fd5e50d1f.png)


Telemetry data of custom format:

```
temp=int.from_bytes(advatc[6:8], byteorder='little', signed=True)/100.0
humidity=int.from_bytes(advatc[8:10], byteorder='little', signed=True)/100.0
batteryv=int.from_bytes(advatc[10:12], byteorder='little', signed=False)
battery=int.from_bytes(advatc[12:13], byteorder='little', signed=False)    
count=int.from_bytes(advatc[13:14], byteorder='little', signed=False) 
flag=int.from_bytes(advatc[14:15], byteorder='little', signed=False) 
```
