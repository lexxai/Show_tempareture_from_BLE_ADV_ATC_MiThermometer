import argparse
import asyncio
import logging

from env_settings import settings

from notifications import (
    DicordNotification,
    LoggerNotification,
)

from outputs import ConsolePrint

from blescanner import BLEScanner


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


async def main(
    custom_names: dict = None,
    alert_low_threshold: float = None,
    alert_high_threshold: float = None,
    use_text_pos: bool = False,
    sent_theshold_temp: float = None,
    mode: str = None,
):
    output = ConsolePrint()
    notification = [LoggerNotification(), DicordNotification()]
    scanner = BLEScanner(
        output=output,
        notification=notification,
        custom_names=custom_names,
        alert_low_threshold=alert_low_threshold,
        alert_high_threshold=alert_high_threshold,
        use_text_pos=use_text_pos,
        sent_theshold_temp=sent_theshold_temp,
        mode=mode,
    )
    params = []
    if custom_names:
        params.append(f"custom_names={custom_names}")
    if alert_low_threshold:
        params.append(f"alert_low_threshold={alert_low_threshold}")
    if alert_high_threshold:
        params.append(f"alert_high_threshold={alert_high_threshold}")
    if sent_theshold_temp:
        params.append(f"sent_theshold_temp={sent_theshold_temp}")

    params.append(f"use_text_pos={use_text_pos}")

    message = ", ".join(params)
    LoggerNotification.send_alert(title="BLE Scanner started with:", message=message)
    try:
        await scanner.start_scanning()
    except asyncio.CancelledError:
        print("Scanning cancelled.")
        scanner.stop_event.set()


if __name__ == "__main__":

    custom_names_default = (
        " ".join(
            [f"{key}='{value}'" for key, value in settings.ATC_CUSTOM_NAMES.items()]
        )
        or "not used"
    )
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Show temperature and humidity from BLE ADV 'ATC MiThermometer' and alarm on temperature."
    )
    parser.add_argument(
        "--names",
        nargs="+",
        help=f'Define custom names in the format KEY=VALUE, where KEY can match with end of device name (e.g., 12345="OUTSIDE"). Default is {custom_names_default}.',
    )
    parser.add_argument(
        "--alert-low-threshold",
        type=lambda x: float(x) if x.lower() != "none" else None,
        default=settings.ALERT_LOW_THRESHOLD,
        help=f"Set the temperature alert threshold less than (e.g., 5.0 for 5°C). Use 'None' to disable. Default is {settings.ALERT_LOW_THRESHOLD}.",
    )

    parser.add_argument(
        "--alert-high-threshold",
        type=lambda x: float(x) if x.lower() != "none" else None,
        default=settings.ALERT_HIGH_THRESHOLD,
        help=f"Set the temperature alert threshold higher than (e.g., 40.0 for 40°C). Use 'None' to disable.  Default is {settings.ALERT_HIGH_THRESHOLD}.",
    )
    parser.add_argument(
        "--sent_theshold_temp",
        type=float,
        default=settings.SENT_TRGESHOLD_TEMP,
        help=f"Set the delta temperature alert threshold for send next notification. Default is {settings.SENT_TRGESHOLD_TEMP}.",
    )
    parser.add_argument(
        "--disable_text_pos",
        help=f"Used when need to disable use text position and use plain print. Default is enabled.",
        action="store_false",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "passive", "active"],
        default="auto",
        help="Select scan mode. Default is 'auto'.",
    )

    args = parser.parse_args()

    # Parse the provided ATC names into a dictionary
    custom_names = None
    if args.names:
        custom_names = {}
        for entry in args.names:
            try:
                key, value = entry.split("=")
                custom_names[key.strip()] = value.strip()
            except ValueError:
                logger.error(f"Invalid entry format: {entry}. Expected KEY=VALUE.")

    # if custom_names:
    #     logger.debug(f"Custom Names: {custom_names}")

    asyncio.run(
        main(
            custom_names=custom_names or settings.ATC_CUSTOM_NAMES,
            alert_low_threshold=args.alert_low_threshold,
            alert_high_threshold=args.alert_high_threshold,
            use_text_pos=args.disable_text_pos,
            sent_theshold_temp=args.sent_theshold_temp,
            mode=args.mode,
        )
    )
