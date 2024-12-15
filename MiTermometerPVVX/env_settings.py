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

    def _initialize(self):
        # Load .env file
        load_dotenv()

        # Read settings from environment
        self.ATC_CUSTOM_NAMES = {
            "5EDB77": "OUTSIDE ROOM",
            "F6ED7A": "MAIN ROOM",
            "995B": "MAIN ROOM",
        }

        self.DISCORD_WEB_HOOKS = os.getenv("DISCORD_WEB_HOOKS")


# Example usage
settings = Settings()
# print(settings.DISCORD_WEB_HOOKS)
# print(settings.ATC_CUSTOM_NAMES)
