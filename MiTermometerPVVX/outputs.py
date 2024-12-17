import asyncio
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(f"BLEScanner.{__name__}")


class AsyncWithDummy(asyncio.Lock):
    async def __aenter__(self):
        """Called when entering the async context."""
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Called when exiting the async context."""
        return True  # Suppress exceptions if needed (returning True does this)


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
    def __init__(self, lock: asyncio.Lock = None):
        super().__init__()
        self.print_method = print

    def format_text(self, text: str, pos: dict = None):
        """Format the text with position if provided."""
        if pos is not None:
            return f'\033[{str(pos["y"])};{str(pos["x"])}H{text}'
        return text

    async def print_value(self, text: str, pos: dict = None) -> None:
        self.print_method(self.format_text(text, pos))

    async def clear(self):
        self.print_method("\033c\033[3J")

    async def clear_lines(self, lines: int = 1):
        for _ in range(lines):
            self.print_method("\033[K")


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
        await self.print_method("\033c\033[3J")

    async def clear_lines(self, lines: int = 1):
        for _ in range(lines):
            await self.print_method("\033[K")

    async def close(self):
        """Gracefully shutdown the worker task and queue."""
        await self.print_queue.put(None)  # Send exit signal to worker
        await self.worker_task
