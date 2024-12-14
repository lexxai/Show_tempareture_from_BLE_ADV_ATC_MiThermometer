import argparse
import asyncio
import datetime
import logging
from bleak import BleakScanner, BleakError

from abstract import ConsolePrint, LoggerNotification, NotificationAbstract, PrintAbstract


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Set the level for the console handler

# Create a formatter and attach it to the console handler
formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
console_handler.setFormatter(formatter)

# Add the console handler to the logger
logger.addHandler(console_handler)


class BLEScanner:
    ALERT_THRESHOLD = 6.0  # Set the temperature threshold (in °C) for alerts
    ATC_CUSTOM_NAMES = {
        "ATC_5EDB77": "OUTSIDE ROOM",
        "ATC_F6ED7A": "MAIN ROOM",
        "ATC-1_995B": "MAIN ROOM",
    }

    def __init__(
        self,
        output: PrintAbstract = None,
        notification: NotificationAbstract = None,
        alert_threshold: float = None,
        custom_names: dict = None,
    ):
        self.output = output or ConsolePrint()
        self.ATC_SERVICE = "0000181a-0000-1000-8000-00805f9b34fb"
        self.stop_event = asyncio.Event()
        self.atc_counters = {}
        self.atc_date = {}
        self.atc_custom_names = custom_names or self.ATC_CUSTOM_NAMES.copy()
        self.atc_devices = {}
        self.print_pos = {"x": 0, "y": 0}
        self.alert_threshold = alert_threshold or self.ALERT_THRESHOLD
        self.notification = notification
        assert self.output is not None, "Output is not set"

    def print_text_pos(self, x: int, y: int) -> None:
        """Set the print cursor position."""
        self.print_pos["x"] = x
        self.print_pos["y"] = y

    def print_text(self, text: str) -> None:
        """Print text at the current cursor position."""
        self.output.print_value(
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
        self.output.print_value("\033c\033[3J")

    def custom_name(self, name: str) -> str:
        """Replace default device name with a custom one if available."""
        for template, custom_name in self.atc_custom_names.items():
            if  name == template or name.endswith(template):
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

        # Trigger alert if temperature is below the threshold
        if self.alert_threshold and temp < self.alert_threshold:
            self.send_alert(name, temp)

    def send_alert(
        self,
        device_name: str = None,
        temp: float = None,
        title: str = None,
        message: str = None,
    ) -> None:
        """Sends an alert message."""
        if not self.notification:
            logger.warning("Notification is not available.")
            return

        device_name = device_name or "Unknown Device"
        temp = temp or 999.99
        alert_title = (
            title or f"Temperature Alert for less than {self.alert_threshold}C"
        )
        alert_message = message or f"{device_name}: {temp:.2f} °C"
        # self.output.print_value("\n*** ALERT: Temperature below threshold ***")
        # self.output.print_value(f"Device: {device_name}")
        # self.output.print_value(f"Temperature: {temp:.2f} °C")

        try:
            self.notification.send_alert(alert_title, alert_message)
            # Using plyer for cross-platform notifications
            # notification.notify(
            #     title=alert_title,
            #     message=alert_message,
            #     timeout=10,  # Notification will disappear after 10 seconds
            # )
        except Exception as e:
            logger.error(f"Notification failed: {e}")

    async def start_scanning(self):
        """Start scanning for BLE devices."""
        self.print_clear()
        for mode in ("passive", "active"):
            logger.info(f"Scanning BLE devices in {mode} mode...")
            try:
                async with BleakScanner(
                    self.process_advertising_data, scanning_mode=mode
                ):
                    await self.stop_event.wait()
                    break
            except BleakError as e:
                logger.error(f"Error in {mode} mode: {e}")


async def main(custom_names: dict = None):
    output = ConsolePrint()
    notification = LoggerNotification()
    scanner = BLEScanner(
        output=output, notification=notification, custom_names=custom_names
    )
    scanner.send_alert(title="MAIN", message="Start scanning")
    try:
        await scanner.start_scanning()
    except asyncio.CancelledError:
        print("Scanning cancelled.")
        scanner.stop_event.set()


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Show temperature and humidity from BLE ADV 'ATC MiThermometer'"
    )
    parser.add_argument(
        "--atc-names",
        nargs="+",
        help='Define custom ATC names in the format KEY=VALUE (e.g., ATC_5EDB77="OUTSIDE ROOM").',
    )
    args = parser.parse_args()

    # Parse the provided ATC names into a dictionary
    custom_names = None
    if args.atc_names:
        custom_names = {}
        for entry in args.atc_names:
            try:
                key, value = entry.split("=")
                custom_names[key.strip()] = value.strip()
            except ValueError:
                logger.error(f"Invalid entry format: {entry}. Expected KEY=VALUE.")

    if custom_names:
        logger.debug(f"Custom ATC Names: {custom_names}")

    asyncio.run(main(custom_names=custom_names))
