import argparse
import asyncio
import logging

from abstract import (
    ConsolePrint,
    LoggerNotification,
)

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
):
    output = ConsolePrint()
    notification = LoggerNotification()
    scanner = BLEScanner(
        output=output,
        notification=notification,
        custom_names=custom_names,
        alert_low_threshold=alert_low_threshold,
        alert_high_threshold=alert_high_threshold,
        use_text_pos=use_text_pos,
    )
    params = []
    if custom_names:
        params.append(f"custom_names={custom_names}")
    if alert_low_threshold:
        params.append(f"alert_low_threshold={alert_low_threshold}")

    if alert_high_threshold:
        params.append(f"alert_high_threshold={alert_high_threshold}")

    params.append(f"use_text_pos={use_text_pos}")

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
    parser.add_argument(
        "--disable_text_pos",
        help=f"Used when need to disable use text position and use plain print. Default is enabled.",
        action="store_false",
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
            use_text_pos=args.disable_text_pos,
        )
    )
