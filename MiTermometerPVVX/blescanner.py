import asyncio
import datetime
from bleak import BleakScanner, BleakError
from plyer import notification


class BLEScanner:
    ALERT_THRESHOLD = 34.0  # Set the temperature threshold (in °C) for alerts
    ATC_CUSTOM_NAMES = {"ATC_F8AB88": "OUTSIDE ROOM", "ATC_F6ED7A": "MAIN ROOM"}

    def __init__(self, alert_threshold=ALERT_THRESHOLD, custom_names=None):
        self.ATC_SERVICE = "0000181a-0000-1000-8000-00805f9b34fb"
        self.stop_event = asyncio.Event()
        self.atc_counters = {}
        self.atc_date = {}
        self.atc_custom_names = custom_names or self.ATC_CUSTOM_NAMES.copy()
        self.atc_devices = {}
        self.print_pos = {"x": 0, "y": 0}
        self.alert_threshold = alert_threshold

    def print_text_pos(self, x: int, y: int) -> None:
        """Set the print cursor position."""
        self.print_pos["x"] = x
        self.print_pos["y"] = y

    def print_text(self, text: str) -> None:
        """Print text at the current cursor position."""
        print(
            "\033["
            + str(self.print_pos["y"])
            + ";"
            + str(self.print_pos["x"])
            + "H"
            + text
        )
        self.print_pos["y"] += 1

    def print_clear(self) -> None:
        """Clear the terminal screen."""
        print("\033c\033[3J")

    def custom_name(self, name: str) -> str:
        """Replace default device name with a custom one if available."""
        for template, custom_name in self.atc_custom_names.items():
            if template in name:
                return custom_name
        return name

    def process_advertising_data(self, device, advertising_data):
        """Process BLE advertising data."""
        adv_atc = advertising_data.service_data.get(self.ATC_SERVICE)
        if not adv_atc:
            return

        name = device.name or self.generate_device_name(device)
        stored_device = self.atc_devices.get(device.address)

        if not stored_device:
            self.register_new_device(device, name)
        elif name != stored_device["name"]:
            stored_device["name"] = name

        self.update_device_data(device, advertising_data, adv_atc)

    def register_new_device(self, device, name):
        """Register a new BLE device."""
        if not self.atc_devices:
            self.print_clear()
        self.atc_devices[device.address] = {"name": name, "id": len(self.atc_devices)}

    def generate_device_name(self, device):
        """Generate a default name if none is provided."""
        if ":" in device.address:
            uiid = "".join(device.address.split(":")[-3:])
        else:
            uiid = device.address.split("-")[-1][-6:]
        return self.custom_name("ATC_" + uiid)

    def update_device_data(self, device, advertising_data, adv_atc):
        """Update the data of a registered BLE device."""
        count = int.from_bytes(adv_atc[13:14], byteorder="little", signed=False)
        if self.atc_counters.get(device.address) == count:
            return

        self.atc_counters[device.address] = count
        date_now = datetime.datetime.now()
        date_diff = date_now - self.atc_date.get(device.address, date_now)
        self.atc_date[device.address] = date_now

        temp = int.from_bytes(adv_atc[6:8], byteorder="little", signed=True) / 100.0
        humidity = (
            int.from_bytes(adv_atc[8:10], byteorder="little", signed=True) / 100.0
        )
        battery_v = (
            int.from_bytes(adv_atc[10:12], byteorder="little", signed=False) / 1000.0
        )
        battery = int.from_bytes(adv_atc[12:13], byteorder="little", signed=False)
        rssi = advertising_data.rssi

        self.display_device_info(
            device.address,
            temp,
            humidity,
            battery_v,
            battery,
            rssi,
            count,
            date_now,
            date_diff,
        )

    def display_device_info(
        self,
        address,
        temp,
        humidity,
        battery_v,
        battery,
        rssi,
        count,
        date_now,
        date_diff,
    ):
        """Display formatted device information."""
        device_info = self.atc_devices[address]
        id = device_info["id"]
        name = device_info["name"]

        cols = 4
        text_width = 22
        pos_x = text_width * (id % cols)
        pos_y = 5 * (id // cols) + 1
        self.print_text_pos(pos_x, pos_y)

        self.print_text(f"Device: {name}")
        self.print_text("-" * 18)
        self.print_text(f"Temp: {temp:.2f}°C")
        self.print_text(f"Humidity: {humidity:.2f}%")
        self.print_text(f"Battery: {battery}% ({battery_v}V)")
        self.print_text(f"RSSI: {rssi} dBm")
        self.print_text(f"Count: {count}")
        self.print_text(f"Last Seen: {date_now.strftime('%H:%M:%S')}")
        if date_diff:
            self.print_text(f"Duration: {date_diff}")

    async def start_scanning(self):
        """Start scanning for BLE devices."""
        self.print_clear()
        for mode in ("passive", "active"):
            print(f"Scanning BLE devices in {mode} mode...")
            try:
                async with BleakScanner(
                    self.process_advertising_data, scanning_mode=mode
                ):
                    await self.stop_event.wait()
                    break
            except BleakError as e:
                print(f"Error in {mode} mode: {e}")


async def main():
    scanner = BLEScanner()
    try:
        await scanner.start_scanning()
    except asyncio.CancelledError:
        print("Scanning cancelled.")
        scanner.stop_event.set()


if __name__ == "__main__":
    asyncio.run(main())
