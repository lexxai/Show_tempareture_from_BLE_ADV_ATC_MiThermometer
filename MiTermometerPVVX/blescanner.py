import asyncio
import datetime
from functools import wraps
import logging
from bleak import BleakScanner, BleakError

from notifications import NotificationAbstract, RegisteredNotifications

from outputs import ConsolePrint, PrintAbstract

logger = logging.getLogger(f"BLEScanner.{__name__}")

class BLEScanner:
    # Set the temperature thresholds (in °C) for alerts
    COLS = 4
    TEXT_WIDTH = 30
    LINE_HEIGHT = 5
    SENT_TRGESHOLD_TEMP = 1
    ATC_SERVICE = "0000181a-0000-1000-8000-00805f9b34fb"

    def __init__(
        self,
        output: PrintAbstract = None,
        notification: RegisteredNotifications = None,
        alert_low_threshold: float = None,
        custom_names: dict = None,
        alert_high_threshold: float = None,
        use_text_pos: bool = True,
        sent_theshold_temp: float = SENT_TRGESHOLD_TEMP,
        mode: str = "auto",  # all, passive, active
    ):
        self.output = output or ConsolePrint()
        self.stop_event = asyncio.Event()
        self.atc_counters = {}
        self.atc_date = {}
        self.atc_custom_names = custom_names or {}
        self.atc_devices = {}
        self.print_pos = {"x": 0, "y": 0}
        self.alert_low_threshold = alert_low_threshold
        self.alert_high_threshold = alert_high_threshold
        self.notification = notification
        self.use_text_pos = use_text_pos
        self.cache_sented_alert = {}
        self.sent_theshold_temp = sent_theshold_temp
        self.mode = mode
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
        if self.use_text_pos:
            self.shift_text_pos(dy=1)

    def print_clear(self) -> None:
        """Clear the terminal screen."""
        if self.use_text_pos:
            self.output.clear()

    def custom_name(self, name: str | None) -> str | None:
        """Replace default device name with a custom one if available."""
        if name:
            for template, custom_name in self.atc_custom_names.items():
                if name.endswith(template) or name == template:
                    return custom_name
        return name

    async def process_advertising_data(self, device, advertising_data):
        """Process BLE advertising data."""
        adv_atc = advertising_data.service_data.get(self.ATC_SERVICE)
        if not adv_atc:
            return

        name = self.custom_name(device.name) or self.generate_device_name(device)
        stored_device = self.atc_devices.get(device.address)

        if not stored_device:
            self.register_new_device(device, name)
        elif name != stored_device["name"]:
            stored_device["name"] = name

        await self.update_device_data(device, advertising_data, adv_atc)

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

    def get_device_name(self, address) -> str | None:
        """Get the name of a registered BLE device."""

        return self.atc_devices.get(address, {}).get("name")

    async def update_device_data(self, device, advertising_data, adv_atc):
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
        await self.monitor_thresholds(self.get_device_name(device.address), temp)

    def clear_lines(self, lines: int = 1):
        if self.use_text_pos:
            self.output.clear_lines(lines)

    def output_cols(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            address = args[0] if len(args) > 0 else kwargs.get("address")
            if address is not None:
                id = self.atc_devices.get(address, {}).get("id")  # noqa: F841 address
                if id is not None:
                    # if id == 0:
                    #     self.print_clear()
                    pos_x = self.TEXT_WIDTH * (id % self.COLS)
                    pos_y = self.LINE_HEIGHT * (id // self.COLS) + 1
                    self.set_text_pos(pos_x, pos_y)
                    # logger.debug(f"Device ID: {id} {pos_x=} {pos_y=}")

            func(self, *args, **kwargs)

            if address is not None:
                self.shift_text_pos(dy=2)
                self.set_text_pos(x=0)

        return wrapper

    @output_cols
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
        name = self.get_device_name(address)

        self.print_text(f"Device: {name}")
        self.print_text("-" * 21)
        self.print_text(f"Temp: {temp:.2f}°C")
        self.print_text(f"Humidity: {humidity:.2f}%")
        self.print_text(f"Battery: {battery}% ({battery_v}V)")
        self.print_text(f"RSSI: {rssi} dBm")
        self.print_text(f"Count: {count}")
        self.print_text(f"Last Seen: {date_now.strftime('%H:%M:%S')}")
        if date_diff:
            self.print_text(f"Duration: {date_diff}")

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

    async def monitor_thresholds(self, name, temp):
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
            if self.is_need_send_alert(name, temp):
                self.clear_lines(10)
                self.print_text("")
                await self.send_alert(title, message)

    def is_need_send_alert(self, name: str, temp: float) -> bool:
        """
        Checks if it is needed to send an alert message.

        Args:
        name (str): The name of the device.
        temp (float): The current temperature.

        Returns:
        bool: True if an alert message should be sent, False if not.
        """
        if self.cache_sented_alert.get(name):
            delta_temp = abs(self.cache_sented_alert[name] - temp)
            if delta_temp > self.sent_theshold_temp:
                self.cache_sented_alert[name] = temp
                return True
            else:
                # logger.debug(
                #     f"Temperature is not changed so much for notification. {temp=} {delta_temp=}"
                # )
                return False
        self.cache_sented_alert[name] = temp
        return True

    async def send_alert(
        self,
        title: str = None,
        message: str = None,
    ) -> None:
        """Sends an alert message."""
        if not self.notification:
            return
        try:
            await self.notification.send_alert(title, message)
        except Exception as e:
            logger.error(f"Notification failed: {e}")

    async def start_scanning(self):
        """Start scanning for BLE devices."""
        # self.print_clear()
        modes = ("passive", "active") if self.mode.lower() == "auto" else (self.mode,)
        for mode in modes:
            logger.info(f"Scanning BLE devices in {mode} mode...")
            try:
                async with BleakScanner(
                    self.process_advertising_data, scanning_mode=mode
                ):
                    await self.stop_event.wait()
                    break
            except BleakError as e:
                logger.error(f"Error in {mode} mode: {e}")
