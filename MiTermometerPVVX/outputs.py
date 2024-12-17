import asyncio
from abc import ABC, abstractmethod
import logging

from utils import AsyncWithDummy

logger = logging.getLogger(f"BLEScanner.{__name__}")


class PrintAbstract(ABC):
    """
    Abstract base class for PrintAbstract objects.
    """

    @property
    def lock(self) -> AsyncWithDummy:
        """
        A lock object for use when printing.

        Returns:
            AsyncWithDummy: An asyncio lock.
        """
        return AsyncWithDummy()

    @abstractmethod
    async def print_value(self, text: str, pos: dict = None) -> None:
        """
        Print a value at the current position.

        Args:
            text (str): The value to print.
            pos (dict, optional): The position to print at. Defaults to None.
        """
        ...

    @abstractmethod
    async def clear(self) -> None:
        """
        Clear the screen.
        """
        ...

    async def clear_lines(self, lines: int = 1):
        """
        Clear the specified number of lines.

        Args:
            lines (int, optional): The number of lines to clear. Defaults to 1.
        """
        ...

    async def close(self) -> None:
        """
        Close the print object.
        """
        ...


class ConsolePrint(PrintAbstract):
    CLEAR_SCREEN = "\033c\033[3J"
    CLEAR_LINE = "\033[K"
    POSITION = "\033[{y};{x}H{text}"

    def __init__(self, lock: asyncio.Lock = None):
        """
        Initialize the `ConsolePrint` object.

        Args:
            lock (asyncio.Lock, optional): An asyncio lock for use when printing.
                Defaults to None.
        """
        super().__init__()
        self.print_method = print


    def format_text(self, text: str, pos: dict = None):
        """
        Format the given text for terminal display, optionally positioning it.

        Args:
            text (str): The text to be formatted.
            pos (dict, optional): A dictionary containing 'x' and 'y' coordinates
                                  for positioning the text. Defaults to None.

        Returns:
            str: The formatted text, with terminal escape sequences if a position
                 is provided.
        """
        if pos is not None:
            return self.POSITION.format(y=pos["y"], x=pos["x"], text=text)
        return text

    async def print_value(self, text: str, pos: dict = None) -> None:
        """
        Print the given text to the console, optionally at a specified position.

        Args:
            text (str): The text to be printed.
            pos (dict, optional): A dictionary containing 'x' and 'y' coordinates
                                  for positioning the text. Defaults to None.

        Returns:
            None
        """
        self.print_method(self.format_text(text, pos))

    async def clear(self):
        """
        Clear the terminal screen by printing the clear screen escape sequence.

        This method uses the print method specified in the class to execute
        the terminal command that clears the entire screen.
        """
        self.print_method(self.CLEAR_SCREEN)

    async def clear_lines(self, lines: int = 1):
        """
        Clear the specified number of lines on the console.

        This method uses the print method specified in the class to execute
        the terminal command that clears a single line, and repeats this for
        the specified number of lines.

        Args:
            lines (int, optional): The number of lines to clear. Defaults to 1.

        Returns:
            None
        """
        for _ in range(lines):
            self.print_method(self.CLEAR_LINE)


class ConsolePrintAsync(ConsolePrint):
    def __init__(self, lock: asyncio.Lock = None):
        """
        Initialize the asynchronous print class.

        This class is a wrapper around ConsolePrint, and uses an asyncio
        Queue to handle the actual printing of messages. A worker task is
        created to consume the queue and print the messages. The print
        method is replaced with an asynchronous version that adds the
        message to the queue.

        Args:
            lock (asyncio.Lock): The lock to use when accessing the print
                queue. If not provided, a dummy lock is used.
        """
        super().__init__()
        self.print_queue = asyncio.Queue()
        self.worker_task = asyncio.create_task(self.print_worker())
        self.print_method = self.async_print
        self._lock = lock

    @property
    def lock(self) -> asyncio.Lock | AsyncWithDummy:
        return self._lock or AsyncWithDummy()

    async def print_worker(self):
        """
        Print worker task that consumes the print queue.

        This task waits for messages to be put into the print queue and
        prints them to the console. If the message is None, the task
        assumes that this is an exit signal and breaks out of the loop.

        The task is responsible for calling task_done() on the queue after
        printing each message, to allow the queue to be properly drained.
        """
        while True:
            message = await self.print_queue.get()
            if message is None:  # Exit signal
                break
            print(message)  # Perform the actual print operation
            self.print_queue.task_done()

    async def async_print(self, text: str):
        """
        Asynchronous print function that adds a string to the print queue.

        The string is added to the print queue and the print worker task
        will print it when it is consumed from the queue.

        Args:
            text (str): The string to print
        """
        await self.print_queue.put(text)

    async def print_value(self, text: str, pos: dict = None) -> None:
        """
        Asynchronous print function that adds a string to the print queue.

        The string is formatted with any specified position information and
        added to the print queue. The print worker task will print it when it
        is consumed from the queue.

        Args:
            text (str): The string to print
            pos (dict, optional): A dictionary containing 'x' and 'y' coordinates
                                  for positioning the text. Defaults to None.
        """
        await self.print_method(self.format_text(text, pos))

    async def clear(self):
        """
        Clear the terminal screen asynchronously.

        This method adds a clear screen escape sequence to the print queue
        and the print worker task will print it when it is consumed from the
        queue.

        Returns:
            None
        """
        await self.print_method(self.CLEAR_SCREEN)

    async def clear_lines(self, lines: int = 1):
        """
        Clear the specified number of lines on the console asynchronously.

        This method adds clear line escape sequences to the print queue
        for the specified number of lines. The print worker task will print
        them when they are consumed from the queue.

        Args:
            lines (int, optional): The number of lines to clear. Defaults to 1.

        Returns:
            None
        """
        for _ in range(lines):
            await self.print_method(self.CLEAR_LINE)

    async def close(self):
        """
        Gracefully shut down the print worker task.

        This method sends an exit signal to the print worker by placing
        a `None` value in the print queue, indicating that the worker
        should stop processing further messages. It then waits for the
        worker task to complete before returning.

        Returns:
            None
        """
        await self.print_queue.put(None)  # Send exit signal to worker
        await self.worker_task
