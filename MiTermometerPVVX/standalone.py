import asyncio
import datetime

# import os

# import struct
from bleak import BleakScanner, BleakError

# MiTermometerPVVX


async def main():
    ATC_SERVICE = "0000181a-0000-1000-8000-00805f9b34fb"
    stop_event = asyncio.Event()
    atc_counters = {}
    atc_date = {}
    atc_custom_name = {"DB77": "SLEEP ROOM", "995B": "MAIN ROOM"}
    atc_devices = {}
    print_pos = {"x": 0, "y": 0}

    def print_text_pos(x: int, y: int) -> None:
        print_pos["x"] = x
        print_pos["y"] = y

    def print_text(text: str) -> None:
        print("\033[" + str(print_pos["y"]) + ";" + str(print_pos["x"]) + "H" + text)
        print_pos["y"] += 1

    def print_clear() -> None:
        print("\033c\033[3J")

    def custom_name(name: str) -> str:
        for template, custom_name in atc_custom_name.items():
            if template in name:
                name = custom_name
        return name

    def callback(device, advertising_data):
        adv_atc = advertising_data.service_data.get(ATC_SERVICE)
        if not adv_atc:
            return

        # if device.address not in atc_devices:
        #     return
        # print(f"advertising_data:\t  {advertising_data.local_name}", atc_devices)
        if advertising_data:
            name = device.name
            if name:
                name = custom_name(name)
                stored_dev = atc_devices.get(device.address)
                if stored_dev and name != stored_dev["name"]:
                    stored_dev["name"] = name

            if device.address not in atc_devices:
                if len(atc_devices) == 0:
                    print_clear()
                atc_devices[device.address] = {"name": name, "id": len(atc_devices)}
                # print(atc_devices)

            if not name:
                name = atc_devices.get(device.address)["name"]
                if not name:
                    if ":" in device.address:
                        uiid = "".join(device.address.split(":")[-3:])
                    else:
                        uiid = device.address.split("-")[-1][-6:]
                    name = "ATC_" + uiid
                    name = custom_name(name)
                    atc_devices[device.address]["name"] = name

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
                    battery_v = battery_v / 1000.0

                    # print(atc_devices[device.address])
                    id = atc_devices[device.address]["id"]
                    h1 = 10
                    h2 = 10
                    gap = 12
                    name_len = h1 + len(name)
                    text_width = name_len + gap
                    text_hight = 10 + 3
                    cols = 4
                    pos_x = text_width * (id % cols)
                    pos_y = text_hight * (id // cols) + 1
                    print_text_pos(pos_x, pos_y)
                    # print_text(f"{'device:':<{h1}}{name}")
                    print_text("{:<10}{}".format("device:", name))
                    print_text("-" * max(18, name_len))
                    print_text("{:<10}{:<10}".format("temp:", f"{temp:.2f} \xB0C"))
                    print_text("{:<10}{:<10}".format("humidity:", f"{humidity:.2f} %"))
                    print_text("{:<10}{:<10}".format("batteryv:", f"{battery_v} V"))
                    print_text("{:<10}{:<10}".format("battery:", f"{battery} %"))
                    print_text("{:<9}{:<11}".format("rssi:", f"{rssi} dBm"))
                    print_text("{:<10}{:<10}".format("count:", f"{count}"))
                    print_text(
                        "{:<10}{:<10}".format(
                            "time now:", f"{date_now.strftime('%H:%M:%S')}"
                        )
                    )
                    if date_diff:
                        print_text(
                            "{:<10}{:<10}".format("Duration:", f"{str(date_diff)}")
                        )
                    # print_text_pos(0, 14)
                    # print_text("debug:")
                    # print(device.name, advertising_data.local_name, atc_devices)
                    # print_text(' '.join('{}:{:02x}'.format(i,x) for i,x in enumerate(adv_atc)))

    try:
        # mode = "passive"
        # mode = "active"
        print_clear()

        for mode in ("passive", "active"):
            # mode = "active"
            print(
                f"Scanning BLE devices of type 'ATC_MiThermometer (PVVX)' in {mode} mode, please wait..."
            )
            try:
                async with BleakScanner(callback, scanning_mode=mode):
                    await stop_event.wait()
                    break
            except BleakError as e:
                print("error", e)

    except asyncio.CancelledError:
        print("**** task scanner cancelled")
        stop_event.set()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(str(e))
