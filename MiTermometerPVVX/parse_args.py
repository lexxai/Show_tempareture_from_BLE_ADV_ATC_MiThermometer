import argparse

from env_settings import settings
from __init__ import __version__


def parse_args(notification_names=None):
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
        "-n",
        "--names",
        nargs="+",
        help=f'Define custom names in the format KEY=VALUE, where KEY can match with end of device name (e.g., 12345="OUTSIDE"). Default is {custom_names_default}.',
    )
    parser.add_argument(
        "-lt",
        "--alert-low-threshold",
        type=lambda x: float(x) if x.lower() != "none" else None,
        default=settings.ALERT_LOW_THRESHOLD,
        help=f"Set the temperature alert threshold less than (e.g., 5.0 for 5°C). Use 'None' to disable. Default is {settings.ALERT_LOW_THRESHOLD}.",
    )

    parser.add_argument(
        "-ht",
        "--alert-high-threshold",
        type=lambda x: float(x) if x.lower() != "none" else None,
        default=settings.ALERT_HIGH_THRESHOLD,
        help=f"Set the temperature alert threshold higher than (e.g., 40.0 for 40°C). Use 'None' to disable.  Default is {settings.ALERT_HIGH_THRESHOLD}.",
    )
    parser.add_argument(
        "-st",
        "--sent_threshold_temp",
        type=float,
        default=settings.SENT_THRESHOLD_TEMP,
        help=f"Set the delta temperature alert threshold for send next notification. Default is {settings.SENT_THRESHOLD_TEMP}.",
    )
    parser.add_argument(
        "-dtp",
        "--disable_text_pos",
        help=f"Used when need to disable use text position and use plain print. Default is enabled.",
        action="store_false",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["auto", "passive", "active"],
        default=settings.BLE_SCANNER_MODE,
        help=f"Select scan mode. Default is '{settings.BLE_SCANNER_MODE}'.",
    )
    notification_registered_choice = notification_names or []
    notification_registered_choice.append("none")
    notification_registered_default = (
        settings.NOTIFICATION or notification_registered_choice[0:1]
    )
    parser.add_argument(
        "-nt",
        "--notification",
        nargs="+",
        choices=notification_registered_choice,
        default=notification_registered_default,
        help=(
            f"Select notification mode individually or multiple, separated by space. Default is '{notification_registered_default[0]}'. "
        ),
    )
    parser.add_argument(
        "-d",
        "--debug",
        default=settings.DEBUG,
        help=f"Enable debug output. Default is {'enabled' if settings.DEBUG else 'disabled'}.",
        action="store_true",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the version of the application",
    )

    args = parser.parse_args()

    return args
