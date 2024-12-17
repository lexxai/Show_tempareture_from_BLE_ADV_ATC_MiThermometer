import asyncio
from abc import ABC, abstractmethod
import logging
from typing import Protocol, TypeVar

from utils import AsyncWithDummy
from discord_api import send_message as discord_send_message

# from plyer import notification

logger = logging.getLogger(f"BLEScanner.{__name__}")


class NotificationAbstract(ABC):
    def __init__(self) -> None:
        super().__init__()

    @property
    def lock(self) -> AsyncWithDummy:
        return AsyncWithDummy()

    @abstractmethod
    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None:
        """Sends an alert message."""
        ...

    def __str__(self):
        return f"{self.__class__.__name__.split('Notification')[0].lower() or self.__class__.__name__}"

    def __repr__(self):
        return self.__str__()


class LoggerNotification(NotificationAbstract):
    def __init__(self, lock: asyncio.Lock = None) -> None:
        super().__init__()
        self._lock = lock

    @property
    def lock(self) -> asyncio.Lock | AsyncWithDummy:
        return self._lock or AsyncWithDummy()

    # @staticmethod
    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None:
        """Logs a notification message with an optional title and message.

        Args:
            title (str | None): The title of the notification, if provided.
            message (str | None): The message content of the notification, if provided.
        """
        if not self.lock:
            logger.error("LoggerNotification has no lock")
            return
        async with self.lock:
            logger.info("*** START LOGGER NOTIFICATION ***")
            if title:
                logger.info(f"Title: {title}")
            if message:
                logger.info(f"Message: {message}")
            logger.info("*** END LOGGER NOTIFICATION ***")


class PrintNotification(NotificationAbstract):
    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None:
        """Prints a notification message with an optional title and message.

        Args:
            title (str | None): The title of the notification, if provided.
            message (str | None): The message content of the notification, if provided.
        """
        print("\n*** START PRINT NOTIFICATION ***")
        if title:
            print(f"Title: {title}")
        if message:
            print(f"Message: {message}")
        print("*** END PRINT NOTIFICATION ***\n")


class DiscordNotification(NotificationAbstract):

    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None:
        """Sends a notification message to Discord with an optional title and message.

        Args:
            title (str | None): The title of the notification, if provided.
            message (str | None): The message content of the notification, if provided.
        """
        msg_list = []
        if title:
            msg_list.append(title)
        if message:
            msg_list.append(message)

        discord_message = "\n".join(msg_list)
        await discord_send_message(discord_message)


class SystemNotification(NotificationAbstract):
    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None:
        """Sends an alert message."""
        logger.info("*** START SYSTEM NOTIFICATION ***")
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


T = TypeVar("T", bound="TaskProtocol")


class TaskProtocol(Protocol):
    """Base class for notification tasks.

    Defines the interface for a notification task, providing a common API for
    different notification types.

    """

    def __str__(self) -> str: ...

    def __repr__(self) -> str: ...

    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None: ...

    @property
    def lock(self) -> None | asyncio.Lock: ...


class ManagerAbstract:
    """Abstract class to manage notification tasks.

    Provides common methods for registration, un-registration, filtering and
    retrieval of tasks.

    """

    def __init__(self, tasks: list[T]):

        self.tasks = tasks or []

    def get(self) -> list[T]:
        return self.tasks

    def register(self, task: T):
        self.tasks.append(task)

    def unregister(self, name: str | None = None, task: T = None):
        if task:
            self.tasks.remove(task)
            return
        if not name:
            return
        for n in self.tasks:
            if str(n) == name:
                self.tasks.remove(n)
                break

    def filter(self, name: list[str] | None, inplace: bool = True) -> list[T] | None:
        if name:
            tasks = list(filter(lambda n: str(n) in name, self.tasks))
            if inplace:
                self.tasks = tasks
            else:
                return tasks
        return self.tasks or None

    def get_names(self) -> list[str]:
        return [str(n) for n in self.tasks]


class ManagerNotifications(ManagerAbstract):

    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None:
        """
        Sends an alert message to all registered notification tasks.

        Args:
            title (str | None): The title of the notification, if provided.
            message (str | None): The message content of the notification, if provided.

        Returns:
            None
        """
        if not self.tasks:
            return
        for n in self.tasks:
            await n.send_alert(title, message)
