import argparse
import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

from outputs import ConsolePrintAsync
from parse_args import parse_args
from env_settings import settings

from notifications import (
    DiscordNotification,
    LoggerNotification,
    ManagerNotifications,
    SystemNotification,
)

from outputs import ConsolePrint

from blescanner import BLEScanner

print_lock = asyncio.Lock()
try:
    registered_notifications = ManagerNotifications(
        [
            LoggerNotification(print_lock),
            DiscordNotification(),
            SystemNotification(),
        ]
    )
except NameError as e:
    print(f"Error registering notifications: {e} {type(e)}")
    registered_notifications = ManagerNotifications()

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
    queue_console_handler = logging.StreamHandler()
    queue_console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    queue_console_handler.setFormatter(
        logging.Formatter("* Async %(asctime)s [%(levelname)s]: %(message)s")
    )
    # Set up the QueueListener
    listener = QueueListener(que, queue_console_handler, respect_handler_level=True)
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
    sent_threshold_temp: float = None,
    mode: str = None,
    notification: ManagerNotifications = None,
    debug: bool = False,
):
    await safely_start_logger(debug)
    logger = logging.getLogger("BLEScanner")
    # log a message
    logger.debug(f"Main is starting")
    output = ConsolePrintAsync(print_lock)
    logger.debug(f"Selected notification: {notification.get_names()}")
    scanner = BLEScanner(
        output=output,
        notification=notification,
        custom_names=custom_names,
        alert_low_threshold=alert_low_threshold,
        alert_high_threshold=alert_high_threshold,
        use_text_pos=use_text_pos,
        sent_theshold_temp=sent_threshold_temp,
        mode=mode,
    )
    params = []
    if custom_names:
        params.append(f"custom_names={custom_names}")
    if alert_low_threshold:
        params.append(f"alert_low_threshold={alert_low_threshold}")
    if alert_high_threshold:
        params.append(f"alert_high_threshold={alert_high_threshold}")
    if sent_threshold_temp:
        params.append(f"sent_threshold_temp={sent_threshold_temp}")

    params.append(f"use_text_pos={use_text_pos}")

    message = ", ".join(params)
    logger.debug(f"BLE Scanner started with: {message}")
    try:
        await scanner.start_scanning()
    except asyncio.CancelledError:
        logger.info("Scanning cancelled.")
        scanner.stop_event.set()
        await asyncio.sleep(0)
        await output.close()


if __name__ in ["main", "__main__"]:

    args = parse_args(registered_notifications.get_names())

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

    # Clear not used notifications from manager
    registered_notifications.filter(args.notification)

    asyncio.run(
        main(
            custom_names=custom_names or settings.ATC_CUSTOM_NAMES,
            alert_low_threshold=args.alert_low_threshold,
            alert_high_threshold=args.alert_high_threshold,
            use_text_pos=args.disable_text_pos,
            sent_threshold_temp=args.sent_threshold_temp,
            mode=args.mode,
            notification=registered_notifications,
            debug=args.debug or settings.DEBUG,
        )
    )
