import argparse
import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

from env_settings import settings

from notifications import (
    DiscordNotification,
    LoggerNotification,
    RegisteredNotifications,
)

from outputs import ConsolePrint

from blescanner import BLEScanner

try:
    registered_notifications = RegisteredNotifications(
        [LoggerNotification(), DiscordNotification()]
    )
except NameError as e:
    print(f"Error registering notifications: {e} {type(e)}")
    registered_notifications = RegisteredNotifications()

logger = logging.getLogger("BLEScanner.{__name__}")
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("* SYNC MAIN %(asctime)s [%(levelname)s]: %(message)s")
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


# helper coroutine to setup and manage the logger
async def init_logger(debug: bool = False):
    # https://docs.python.org/3/howto/logging-cookbook.html#blocking-handlers
    # https://superfastpython.com/asyncio-log-blocking/
    # Create the shared queue
    que = Queue(-1)
    que_handler = QueueHandler(que)
    # Set up the console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("* Async Queue %(asctime)s [%(levelname)s]: %(message)s")
    )
    # Set up the QueueListener
    listener = QueueListener(que, console_handler, respect_handler_level=True)
    # Configure the root logger
    logger = logging.getLogger("BLEScanner")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(que_handler)
    logger.propagate = False  # Prevent duplicate logs due to propagation
    try:
        # start the listener
        listener.start()
        # report the logger is ready
        logger.debug(f"Logger has started")
        # wait forever
        while True:
            await asyncio.sleep(60)
    finally:
        # report the logger is done
        logger.debug(f"Logger is shutting down")
        # ensure the listener is closed
        listener.stop()

    # reference to the logger task


LOGGER_TASK = None


# coroutine to safely start the logger
async def safely_start_logger(debug: bool = False):
    # initialize the logger
    global LOGGER_TASK
    LOGGER_TASK = asyncio.create_task(init_logger(debug))
    # allow the logger to start
    await asyncio.sleep(0)


async def main(
    custom_names: dict = None,
    alert_low_threshold: float = None,
    alert_high_threshold: float = None,
    use_text_pos: bool = False,
    sent_theshold_temp: float = None,
    mode: str = None,
    notification: RegisteredNotifications = None,
    debug: bool = False,
):
    await safely_start_logger(debug)
    logger = logging.getLogger("BLEScanner")
    # log a message
    logger.debug(f"Main is starting")
    output = ConsolePrint()
    logger.debug(f"Selected notification: {notification.get_notification_names()}")
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
    logger.debug(f"BLE Scanner started with: {message}")
    try:
        await scanner.start_scanning()
    except asyncio.CancelledError:
        logger.info("Scanning cancelled.")
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
    notification_registered_cooise = registered_notifications.get_notification_names()
    notification_registered_cooise.append("none")
    notification_registered_default = notification_registered_cooise[0:1]
    parser.add_argument(
        "--notification",
        nargs="+",
        choices=notification_registered_cooise,
        default=notification_registered_default,
        help=(
            f"Select notification mode individually or multiple, separated by space. Default is '{notification_registered_default[0]}'. "
        ),
    )
    parser.add_argument(
        "--debug",
        help="Enable debug output",
        action="store_true",
    )

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG if args.debug else logging.INFO)

    # Parse the provided ATC names into a dictionary
    custom_names = None
    if args.names:
        custom_names = {}
        for entry in args.names:
            try:
                key, value = entry.split("=")
                custom_names[key.strip()] = value.strip()
            except ValueError:
                logging.error(f"Invalid entry format: {entry}. Expected KEY=VALUE.")

    # if custom_names:
    logger.debug(f"Custom Names: {custom_names}")

    registered_notifications.filer_notifications(args.notification)

    asyncio.run(
        main(
            custom_names=custom_names or settings.ATC_CUSTOM_NAMES,
            alert_low_threshold=args.alert_low_threshold,
            alert_high_threshold=args.alert_high_threshold,
            use_text_pos=args.disable_text_pos,
            sent_theshold_temp=args.sent_theshold_temp,
            mode=args.mode,
            notification=registered_notifications,
            debug=args.debug or settings.DEBUG,
        )
    )
