from abc import ABC, abstractmethod
import logging

from discord_api import send_message as discors_send_message

# from plyer import notification

logger = logging.getLogger(f"BLEScanner.{__name__}")
# logger = None


def init_logger():
    global logger
    logger = logging.getLogger(f"BLEScanner.{__name__}")


class NotificationAbstract(ABC):
    is_async = False

    @abstractmethod
    def send_alert(self, title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        ...

    def __str__(self):
        return f"{self.__class__.__name__.split('Notification')[0].lower() or self.__class__.__name__}"


class LoggerNotification(NotificationAbstract):
    @staticmethod
    def send_alert(title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        logger.info("*** START LOGGER NOTIFICATION ***")
        if title:
            logger.info(f"Title: {title}")
        if message:
            logger.info(f"Message: {message}")
        logger.info("*** END LOGGER NOTIFICATION ***")


class PrintNotification(NotificationAbstract):
    def send_alert(self, title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        print("\n*** START PRINT NOTIFICATION ***")
        if title:
            print(f"Title: {title}")
        if message:
            print(f"Message: {message}")
        print("*** END PRINT NOTIFICATION ***\n")


class DiscordNotification(NotificationAbstract):
    is_async = True

    async def send_alert(self, title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        msg_list = []
        if title:
            msg_list.append(title)
        if message:
            msg_list.append(message)

        discord_message = "\n".join(msg_list)
        await discors_send_message(discord_message)


class SystemNotification(NotificationAbstract):
    def send_alert(self, title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        logger.info("*** START SYETEM NOTIFICATION ***")
        if title:
            logger.info(f"Title: {title}")
        if message:
            logger.info(f"Message: {message}")
        logger.info("*** END SYSTEM NOTIFICATION ***")
        # Using plyer for cross-platform notifications
        # notification.notify(
        #     title=alert_title,
        #     message=alert_message,
        #     timeout=10,  # Notification will disappear after 10 seconds
        # )
