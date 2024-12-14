from abc import ABC, abstractmethod
import logging
# from plyer import notification

logger = logging.getLogger(f"BLEScanner.{__name__}")

class NotificationAbstract(ABC):
    @abstractmethod
    def send_alert(self, title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        ...


class PrintAbstract(ABC):
    @abstractmethod
    def print_value(self, text: str) -> None: ...


class LoggerNotification(NotificationAbstract):

    def send_alert(self, title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        logger.info("*** START LOGGER NOTIFICATION ***")
        logger.info(f"Title: {title}")
        logger.info(f"Message: {message}")
        logger.info("*** END LOGGER NOTIFICATION ***")


class SystemNotification(NotificationAbstract):

    def send_alert(self, title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        logger.info("*** START SYETEM NOTIFICATION ***")
        logger.info(f"Title: {title}")
        logger.info(f"Message: {message}")
        logger.info("*** END SYSTEM NOTIFICATION ***")


class ConsolePrint(PrintAbstract):
    def print_value(self, text: str) -> None:
        print(text)
