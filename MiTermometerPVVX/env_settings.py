import os
from dotenv import load_dotenv
from threading import Lock


class Settings:
    _instance = None
    _lock = Lock()  # For thread-safe singleton

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _load_custom_names(self):
        custom_names = {}
        prefix = "NAME_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove the prefix and use the remaining part as the key
                shortened_key = key[len(prefix) :]
                custom_names[shortened_key] = value
        return custom_names

    def _initialize(self):
        # Load .env file
        load_dotenv()

        self.DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"
        self.ATC_CUSTOM_NAMES = self._load_custom_names()

        self.ALERT_LOW_THRESHOLD = os.getenv("ALERT_LOW_THRESHOLD")
        self.ALERT_HIGH_THRESHOLD = os.getenv("ALERT_HIGH_THRESHOLD")
        self.SENT_THRESHOLD_TEMP = os.getenv("SENT_THRESHOLD_TEMP", 1.0)

        self.DISCORD_WEB_HOOKS = os.getenv("DISCORD_WEB_HOOKS")

        n = os.getenv("NOTIFICATION")
        self.NOTIFICATION = n.split(",") if n else None

        self.BLE_SCANNER_MODE = os.getenv("BLE_SCANNER_MODE", "auto").lower()
        if self.BLE_SCANNER_MODE not in ["auto", "passive", "active"]:
            self.BLE_SCANNER_MODE = "auto"


# Example usage
settings = Settings()
# print(settings.DISCORD_WEB_HOOKS)
# print(settings.ATC_CUSTOM_NAMES)
