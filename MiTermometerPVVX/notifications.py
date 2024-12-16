from abc import ABC, abstractmethod
import logging

from discord_api import send_message as discors_send_message

# from plyer import notification

logger = logging.getLogger(f"BLEScanner.{__name__}")


class NotificationAbstract(ABC):
    is_async = False

    @abstractmethod
    def send_alert(self, title: str = None, message: str = None) -> None:
        """Sends an alert message."""
        ...

    def __str__(self):
        return f"{self.__class__.__name__.split('Notification')[0].lower() or self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()


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
        # Using plyer for cross-platform tasks
        # notification.notify(
        #     title=alert_title,
        #     message=alert_message,
        #     timeout=10,  # Notification will disappear after 10 seconds
        # )


class ManagerAbstract(ABC):
    def __init__(self, tasks: list[NotificationAbstract]):
        self.tasks = tasks or []

    def get(self) -> list[NotificationAbstract]:
        return self.tasks

    def register(self, notification: NotificationAbstract):
        self.tasks.append(notification)

    def unregister(self, name: str):
        for n in self.tasks:
            if str(n) == name:
                self.tasks.remove(n)
                break

    def filer(self, name: list[str]) -> list[NotificationAbstract]:
        if name:
            self.tasks = list(
                filter(lambda n: str(n) in name, self.tasks)
            )
        return self.tasks or None

    def get_names(self) -> list[str]:
        return [str(n) for n in self.tasks]

class ManagerNotifications(ManagerAbstract):

    async def send_alert(self, title: str = None, message: str = None) -> None:
        if not self.tasks:
            return
        for n in self.tasks:
            if n.is_async:
                await n.send_alert(title, message)
            else:
                n.send_alert(title, message)
