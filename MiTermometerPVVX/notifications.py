import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Protocol, TypeVar

from plyer import notification

from env_settings import settings
from utils import AsyncWithDummy
from discord_api import send_message as discord_send_message

# from plyer import notification

logger = logging.getLogger(f"BLEScanner.{__name__}")


class NotificationAbstract(ABC):
    """
    Abstract base class for notifications.

    Provides a blueprint for notification classes with a lock property
    and an abstract method to send alert messages.
    """

    def __init__(self) -> None:
        """
        Initializes the NotificationAbstract class.
        """
        super().__init__()

    @property
    def lock(self) -> AsyncWithDummy:
        """
        Returns a lock object for use when sending notifications.

        Returns:
            AsyncWithDummy: An asyncio lock.
        """
        return AsyncWithDummy()

    @abstractmethod
    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None:
        """
        Sends an alert message.

        Args:
            title (str | None): The title of the notification, if provided.
            message (str | None): The message content of the notification, if provided.
        """
        ...

    def __str__(self) -> str:
        """
        Returns a string representation of the class.

        Returns:
            str: The class name in lowercase without 'Notification'.
        """
        return f"{self.__class__.__name__.split('Notification')[0].lower() or self.__class__.__name__}"

    def __repr__(self) -> str:
        """
        Returns a string representation of the class for debugging.

        Returns:
            str: The class name in lowercase without 'Notification'.
        """
        return self.__str__()

    """
    A Notification class that logs messages to the logger.

    This class logs message with the INFO level and can be used to log messages
    without sending any notifications.

    Attributes:
        _lock (asyncio.Lock | AsyncWithDummy): The lock to use when sending
            notifications. If not provided, a dummy lock is used.
    """


class LoggerNotification(NotificationAbstract):
    def __init__(self, lock: asyncio.Lock = None) -> None:
        """
        Initializes the LoggerNotification object.

        Args:
            lock (asyncio.Lock | AsyncWithDummy): The lock to use when sending
                notifications. If not provided, a dummy lock is used.
        """
        super().__init__()
        self._lock = lock

    @property
    def lock(self) -> asyncio.Lock | AsyncWithDummy:
        """
        Returns the lock object for use when sending notifications.

        If no lock is provided, a dummy lock is used.

        Returns:
            asyncio.Lock | AsyncWithDummy: The lock object to use when sending
                notifications.
        """
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
    def __init__(self, timeout: int = None):
        super().__init__()
        self.timeout = timeout or 30
        self.icon = str(settings.BASE_PATH.parent.joinpath("icon-64x64.ico"))
        self.app_name = settings.APP_NAME

    async def send_alert(
        self, title: str | None = None, message: str | None = None
    ) -> None:
        """Sends an alert message."""
        logger.debug("*** START SYSTEM NOTIFICATION ***")
        await asyncio.to_thread(
            notification.notify,
            title=title,
            message=message,
            timeout=self.timeout,
            app_name=self.app_name,
            app_icon=self.icon,
        )
        logger.debug("*** END SYSTEM NOTIFICATION ***")


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
        """Initialize ManagerAbstract with a list of tasks.

        Args:
            tasks (list[T]): A list of notification tasks.

        """
        self.tasks = tasks or []

    def get(self) -> list[T]:
        """Get the list of tasks.

        Returns:
            list[T]: The list of tasks.

        """
        return self.tasks

    def register(self, task: T):
        """Register a task.

        Args:
            task (T): The task to be registered.

        """
        self.tasks.append(task)

    def unregister(self, name: str | None = None, task: T = None):
        """Unregister a task.

        Args:
            name (str | None): The name of the task to be unregistered.
                If None, the task object must be provided.
            task (T): The task object to be unregistered.

        """
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
        """
        Filter tasks by their names.

        Args:
            name (list[str] | None): List of task names to filter by.
            inplace (bool): If True, update the current task list in place.

        Returns:
            list[T] | None: The filtered list of tasks, or None if no tasks exist.
        """
        if name:
            tasks = list(filter(lambda n: str(n) in name, self.tasks))
            if inplace:
                self.tasks = tasks
            else:
                return tasks
        return self.tasks or None

    def get_names(self) -> list[str]:
        """
        Retrieve the names of all registered tasks.

        Returns:
            list[str]: A list of task names.
        """
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
