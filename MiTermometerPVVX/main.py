import argparse
import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

from env_settings import settings

from notifications import (
    DiscordNotification,
    LoggerNotification,
)

from outputs import ConsolePrint

from blescanner import BLEScanner

try:
    REGISTERED_NOTIFICATIONS = [LoggerNotification(), DiscordNotification()]
except NameError as e:
    print(f"Error registering notifications: {e} {type(e)}")
    REGISTERED_NOTIFICATIONS = []

# print(f"Registered notifications: {[str(n) for n in REGISTERED_NOTIFICATIONS]}")

# logger = logging.getLogger("_BLEScanner")
# logger.setLevel(logging.ERROR)
# console_handler = logging.StreamHandler()
# # console_handler.setLevel(logging.ERROR)
# formatter = logging.Formatter("* SYNC MAIN %(asctime)s [%(levelname)s]: %(message)s")
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)

# # Ensure child loggers propagate messages
# for child_logger_name in ["BLEScanner.notifications", "BLEScanner.blescanner"]:
#     child_logger = logging.getLogger(child_logger_name)
#     child_logger.propagate = True
#     child_logger.handlers = []

# logger = logging.getLogger("BLEScanner")
# logger.setLevel(logging.DEBUG)

# # Create a console handler
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)  # Set the level for the console handler

# # Create a formatter and attach it to the console handler
# formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
# console_handler.setFormatter(formatter)

# # Add the console handler to the logger
# logger.addHandler(console_handler)


# helper coroutine to setup and manage the logger
async def init_logger():
    # get the root logger
    log = logging.getLogger("BLEScanner")
    # create the shared queue
    que = Queue()
    # add a handler that uses the shared queue
    que_handler = QueueHandler(que)
    # # Create a formatter and attach it to the que_handler
    formatter = logging.Formatter(
        "* Async Queue %(asctime)s [%(levelname)s]: %(message)s"
    )
    que_handler.setFormatter(formatter)
    log.addHandler(que_handler)
    # log all messages, debug and up
    log.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.ERROR)
    # # Create a formatter and attach it to the console handler
    # formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s")
    # console_handler.setFormatter(formatter)
    # create a listener for messages on the queue
    listener = QueueListener(que, logging.StreamHandler())
    try:
        # start the listener
        listener.start()
        # report the logger is ready
        log.debug(f"Logger has started")
        # wait forever
        while True:
            await asyncio.sleep(60)
    finally:
        # report the logger is done
        log.debug(f"Logger is shutting down")
        # ensure the listener is closed
        listener.stop()

    # reference to the logger task


LOGGER_TASK = None


def modules_init_logger():
    import sys

    modules = ["notifications", "blescanner"]
    for module_name in modules:
        try:
            # Check if the module is already imported
            if module_name in sys.modules:
                module = sys.modules[module_name]  # Get the module from sys.modules

                # Call the init_logger method if it exists
                if hasattr(module, "init_logger"):
                    getattr(module, "init_logger")()  # Calls module.init_logger()
                else:
                    print(f"Module {module_name} does not have 'init_logger' method.")
            else:
                print(f"Module {module_name} is not imported.")
        except Exception as e:
            print(f"Error calling 'init_logger' in module {module_name}: {e}")


# coroutine to safely start the logger
async def safely_start_logger():
    # initialize the logger
    global LOGGER_TASK
    LOGGER_TASK = asyncio.create_task(init_logger())
    # allow the logger to start
    await asyncio.sleep(1)


async def main(
    custom_names: dict = None,
    alert_low_threshold: float = None,
    alert_high_threshold: float = None,
    use_text_pos: bool = False,
    sent_theshold_temp: float = None,
    mode: str = None,
    notification: list[str] = None,
):
    await safely_start_logger()
    # log a message
    logging.info(f"Main is starting")
    output = ConsolePrint()
    _notification = []
    # Build list of selected notifications
    registered_names = [str(n) for n in REGISTERED_NOTIFICATIONS]
    for n in notification:
        if n in registered_names:
            _notification.append(n)
    if len(_notification) == 0:
        _notification = None
    print(f"Selected notification: {_notification}")
    # _notification = [LoggerNotification(), DicordNotification()]
    scanner = BLEScanner(
        output=output,
        notification=_notification,
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
    logging.info(f"BLE Scanner started with: {message}")
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
    notification_registered_cooise = [str(n) for n in REGISTERED_NOTIFICATIONS]
    notification_registered_cooise.append("none")
    notification_registered_default = notification_registered_cooise[0:1]
    parser.add_argument(
        "--notification",
        nargs="+",
        choices=notification_registered_cooise,
        default=notification_registered_default,
        help=(
            f"Select notification mode as individualy as and multiple. Default is '{notification_registered_default[0]}'. "
        ),
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
                logging.error(f"Invalid entry format: {entry}. Expected KEY=VALUE.")

    # if custom_names:
    logging.info(f"Custom Names: {custom_names}")

    asyncio.run(
        main(
            custom_names=custom_names or settings.ATC_CUSTOM_NAMES,
            alert_low_threshold=args.alert_low_threshold,
            alert_high_threshold=args.alert_high_threshold,
            use_text_pos=args.disable_text_pos,
            sent_theshold_temp=args.sent_theshold_temp,
            mode=args.mode,
            notification=args.notification,
        )
    )
