import asyncio
from abc import ABC, abstractmethod
import logging

from utils import AsyncWithDummy

logger = logging.getLogger(f"BLEScanner.{__name__}")


class PrintAbstract(ABC):

    @property
    def lock(self) -> AsyncWithDummy:
        return AsyncWithDummy()

    @abstractmethod
    async def print_value(self, text: str, pos: dict = None) -> None: ...

    @abstractmethod
    async def clear(self) -> None: ...

    async def clear_lines(self, lines: int = 1): ...


class ConsolePrint(PrintAbstract):
    CLEAR_SCREEN = "\033c\033[3J"
    CLEAR_LINE = "\033[K"
    POSITION = "\033[{y};{x}H{text}"

    def __init__(self, lock: asyncio.Lock = None):
        super().__init__()
        self.print_method = print

    def format_text(self, text: str, pos: dict = None):
        """Format the text with position if provided."""
        if pos is not None:
            return self.POSITION.format(y=pos["y"], x=pos["x"], text=text)
        return text

    async def print_value(self, text: str, pos: dict = None) -> None:
        self.print_method(self.format_text(text, pos))

    async def clear(self):
        self.print_method(self.CLEAR_SCREEN)

    async def clear_lines(self, lines: int = 1):
        for _ in range(lines):
            self.print_method(self.CLEAR_LINE)


class ConsolePrintAsync(ConsolePrint):
    def __init__(self, lock: asyncio.Lock = None):
        super().__init__()
        self.print_queue = asyncio.Queue()
        self.worker_task = asyncio.create_task(self.print_worker())
        self.print_method = self.async_print
        self._lock = lock

    @property
    def lock(self) -> asyncio.Lock | AsyncWithDummy:
        return self._lock or AsyncWithDummy()

    async def print_worker(self):
        """Worker that processes messages from the print queue."""
        while True:
            message = await self.print_queue.get()
            if message is None:  # Exit signal
                break
            print(message)  # Perform the actual print operation
            self.print_queue.task_done()

    async def async_print(self, text: str):
        """Put messages into the print queue."""
        await self.print_queue.put(text)

    async def print_value(self, text: str, pos: dict = None) -> None:
        await self.print_method(self.format_text(text, pos))

    async def clear(self):
        await self.print_method(self.CLEAR_SCREEN)

    async def clear_lines(self, lines: int = 1):
        for _ in range(lines):
            await self.print_method(self.CLEAR_LINE)

    async def close(self):
        """Gracefully shutdown the worker task and queue."""
        await self.print_queue.put(None)  # Send exit signal to worker
        await self.worker_task
