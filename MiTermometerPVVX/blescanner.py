import argparse
import asyncio
import datetime
import logging
from bleak import BleakScanner, BleakError

from abstract import (
    ConsolePrint,
    LoggerNotification,
    NotificationAbstract,
    PrintNotification,
    PrintAbstract,
)


logger = logging.getLogger("BLEScanner")
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
    # Set the temperature thresholds (in °C) for alerts
    ALERT_LOW_THRESHOLD = 6.0
    ALERT_HIGH_THRESHOLD = 36.0
    COLS = 4
    TEXT_WIDTH = 24

    ATC_CUSTOM_NAMES = {
        "5EDB77": "OUTSIDE ROOM",
        "F6ED7A": "MAIN ROOM",
        "995B": "MAIN ROOM",
    }

    def __init__(
        self,
        output: PrintAbstract = None,
        notification: NotificationAbstract = None,
        alert_low_threshold: float = None,
        custom_names: dict = None,
        alert_high_threshold: float = None,
    ):
        self.output = output or ConsolePrint()
        self.ATC_SERVICE = "0000181a-0000-1000-8000-00805f9b34fb"
        self.stop_event = asyncio.Event()
        self.atc_counters = {}
        self.atc_date = {}
        self.atc_custom_names = custom_names or self.ATC_CUSTOM_NAMES.copy()
        self.atc_devices = {}
        self.print_pos = {"x": 0, "y": 0}
        self.alert_low_threshold = alert_low_threshold or self.ALERT_LOW_THRESHOLD
        self.alert_high_threshold = alert_high_threshold or self.ALERT_HIGH_THRESHOLD
        self.notification = notification
        self.use_text_pos = False
        assert self.output is not None, "Output is not set"

    def set_text_pos(self, x: int = None, y: int = None) -> None:
        """Set the print cursor position."""
        if x is not None:
            self.print_pos["x"] = x
        if y is not None:
            self.print_pos["y"] = y

    def shift_text_pos(self, dx: int = None, dy: int = None) -> None:
        if dx:
            self.print_pos["x"] += dx
        if dy:
            self.print_pos["y"] += dy

    def get_text_pos_dict(self) -> dict:
        return self.print_pos.copy()

    def print_text(self, text: str) -> None:
        """Print text at the current cursor position."""
        pos = self.get_text_pos_dict() if self.use_text_pos else None
        self.output.print_value(text, pos=pos)
        self.shift_text_pos(dy=1)

    def print_clear(self) -> None:
        """Clear the terminal screen."""
        if self.use_text_pos:
            self.output.clear()

    def custom_name(self, name: str) -> str:
        """Replace default device name with a custom one if available."""
        logger.debug(f"custom_name in: {name}")
        for template, custom_name in self.atc_custom_names.items():
            if name.endswith(template) or name == template:
                logger.debug(f"custom_name out: {custom_name}")
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

        cols = self.COLS
        text_width = self.TEXT_WIDTH
        pos_x = text_width * (id % cols)
        pos_y = 5 * (id // cols) + 1
        self.set_text_pos(pos_x, pos_y)

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
        self.print_pos["y"] += 2
        self.print_pos["x"] = 0
        self.print_text("")
        self.monitor_thresholds(name, temp)

    def generate_title_message(
        self,
        device_name: str = None,
        temp: float = None,
        threshold_type: int = 0,  # 0 = lower, 2 - higher
        threshold_value: float = None,
    ) -> tuple:
        device_name = device_name or "Unknown Device"
        threshold_text = "lower" if threshold_type == 0 else "higher"
        threshold_value_text = (
            f"{threshold_value} °C" if threshold_value else "threshold value"
        )
        title = f"Temperature Alert for {threshold_text} than {threshold_value_text}"
        message = f"{device_name}: {temp:.2f} °C" if temp else None

        return title, message

    def monitor_thresholds(self, name, temp):
        title, message = None, None
        # Trigger alert if temperature is below the threshold
        if self.alert_low_threshold is not None and temp <= self.alert_low_threshold:
            title, message = self.generate_title_message(
                name, temp, threshold_type=0, threshold_value=self.alert_low_threshold
            )
        # Trigger alert if temperature is higher than the threshold
        if self.alert_high_threshold is not None and temp >= self.alert_high_threshold:
            title, message = self.generate_title_message(
                name, temp, threshold_type=2, threshold_value=self.alert_high_threshold
            )
        if title or message:
            self.send_alert(title, message)

    def send_alert(
        self,
        title: str = None,
        message: str = None,
    ) -> None:
        """Sends an alert message."""
        if not self.notification:
            logger.warning("Notification is not available.")
            return
        try:
            self.notification.send_alert(title, message)
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


async def main(
    custom_names: dict = None,
    alert_low_threshold: float = None,
    alert_high_threshold: float = None,
):
    output = ConsolePrint()
    notification = LoggerNotification()
    scanner = BLEScanner(
        output=output,
        notification=notification,
        custom_names=custom_names,
        alert_low_threshold=alert_low_threshold,
        alert_high_threshold=alert_high_threshold,
    )
    params = []
    if custom_names:
        params.append(f"custom_names={custom_names}")
    if alert_low_threshold:
        params.append(f"alert_low_threshold={alert_low_threshold}")

    if alert_high_threshold:
        params.append(f"alert_high_threshold={alert_high_threshold}")

    message = ", ".join(params)
    scanner.send_alert(title="BLE Scanner started with:", message=message)
    try:
        await scanner.start_scanning()
    except asyncio.CancelledError:
        print("Scanning cancelled.")
        scanner.stop_event.set()


if __name__ == "__main__":

    custom_names_default = " ".join(
        [f"{key}='{value}'" for key, value in BLEScanner.ATC_CUSTOM_NAMES.items()]
    )
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Show temperature and humidity from BLE ADV 'ATC MiThermometer'"
    )
    parser.add_argument(
        "--atc-names",
        nargs="+",
        help=f'Define custom ATC names in the format KEY=VALUE, where KEY can match with end of device name (e.g., ATC_12345="OUTSIDE"). Default is "{custom_names_default}".',
    )
    parser.add_argument(
        "--alert-low-threshold",
        type=float,
        help=f"Set the temperature alert threshold less than (e.g., 5.0 for 5°C). Default is {BLEScanner.ALERT_LOW_THRESHOLD}°C.",
    )

    parser.add_argument(
        "--alert-high-threshold",
        type=float,
        help=f"Set the temperature alert threshold higher than (e.g., 40.0 for 40°C). Default is {BLEScanner.ALERT_HIGH_THRESHOLD}°C.",
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

    asyncio.run(
        main(
            custom_names=custom_names,
            alert_low_threshold=args.alert_low_threshold,
            alert_high_threshold=args.alert_high_threshold,
        )
    )
