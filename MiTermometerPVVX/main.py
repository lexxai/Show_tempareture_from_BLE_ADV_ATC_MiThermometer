import asyncio
import datetime

# import struct
from bleak import BleakScanner

# MiTermometerPVVX


async def main():
    ATC_SERVICE = "0000181a-0000-1000-8000-00805f9b34fb"
    stop_event = asyncio.Event()
    atc_counters = {}
    atc_date = {}
    # atc_devices = {"00:00:00:00:99:5B": "ATC-1-995B", "00:00:00:00:DB:77": "ATC-2-DB77"}
    atc_devices = {}

    def callback(device, advertising_data):
        adv_atc = advertising_data.service_data.get(ATC_SERVICE)
        if not adv_atc:
            return

        # if device.address not in atc_devices:
        #     return
        # print("device:\t", device)
        # print(f"advertising_data:\t  {advertising_data}")
        if advertising_data:
            name = advertising_data.local_name

            if device.address not in atc_devices:
                atc_devices[device.address] = name

            if not name:
                name = atc_devices.get(device.address)
                if not name:
                    name = "ATC-" + "".join(device.address.split(":")[-2:])
                    atc_devices[device.address] = name
        # print(atc_devices)
        # if name and name[0:3] == "ATC":
        if True:
            rssi = advertising_data.rssi
            # adv_atc = advertising_data.service_data[ATC_SERVICE]
            if adv_atc:
                count = int.from_bytes(adv_atc[13:14], byteorder="little", signed=False)
                # (temp,humidity,battery_v,battery,count) = struct.unpack('<hhHBB',adv_atc[6:14])
                if atc_counters.get(device.address) != count:
                    atc_counters.update({device.address: count})
                    date_now = datetime.datetime.now()
                    date_prev = atc_date.get(device.address)
                    if date_prev:
                        date_diff = date_now - date_prev
                        date_diff = datetime.timedelta(
                            seconds=round(date_diff.total_seconds())
                        )
                    else:
                        date_diff = 0
                    atc_date.update({device.address: date_now})
                    temp = int.from_bytes(adv_atc[6:8], byteorder="little", signed=True)
                    humidity = int.from_bytes(
                        adv_atc[8:10], byteorder="little", signed=True
                    )
                    battery_v = int.from_bytes(
                        adv_atc[10:12], byteorder="little", signed=False
                    )
                    battery = int.from_bytes(
                        adv_atc[12:13], byteorder="little", signed=False
                    )
                    # flag=int.from_bytes(adv_atc[14:15], byteorder='little', signed=False)
                    temp = temp / 100.0
                    humidity = humidity / 100.0
                    print()
                    print(f"device:\t  {name}")
                    name_len = len(str(name)) + 10
                    print("-" * name_len)
                    print(f"temp:\t  {temp}\xB0C")
                    print(f"humidity: {humidity}%")
                    print(f"batteryv: {battery_v} mV")
                    print(f"battery:  {battery}%")
                    print(f"count:\t  {count}")
                    print(f"rssi:     {rssi}")
                    if date_diff:
                        date_diff_text = ", duration: " + str(date_diff)
                    else:
                        date_diff_text = ""
                    print(f'time now: {date_now.strftime("%H:%M:%S")}{date_diff_text}')

    try:
        mode = "passive"
        # mode = "active"
        async with BleakScanner(callback, scanning_mode=mode):
            await stop_event.wait()
    except asyncio.CancelledError:
        print("**** task scanner cancelled")
        stop_event.set()


if __name__ == "__main__":
    print("Scanning BLE devices of type 'ATC_MiThermometer (PVVX)', please wait...")
    try:
        asyncio.run(main())
    except Exception as e:
        print(str(e))
