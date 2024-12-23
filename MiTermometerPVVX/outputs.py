import asyncio
from abc import ABC, abstractmethod
import logging
import os

from utils import AsyncWithDummy

logger = logging.getLogger(f"BLEScanner.{__name__}")


class PrintAbstract(ABC):
    """
    Abstract base class for PrintAbstract objects.
    """

    @property
    def lock(self) -> asyncio.Lock:
        """
        A lock object for use when printing.

        Returns:
            asyncio.Lock: An asyncio lock.
        """
        return asyncio.Lock()

    @abstractmethod
    async def print_value(self, text: str, pos: dict = None) -> None:
        """
        Print a value at the current position.

        Args:
            text (str): The value to print.
            pos (dict, optional): The position to print at. Defaults to None.
                                  Positioning starts at 0.
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
                                  Positioning starts at 0.

        Returns:
            str: The formatted text, with terminal escape sequences if a position
                 is provided.
        """
        if pos is not None:
            return self.POSITION.format(y=pos["y"] + 1, x=pos["x"] + 1, text=text)
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
    def lock(self) -> asyncio.Lock:
        return self._lock or asyncio.Lock()

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
                                  Positioning starts at 0.
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


class ConsoleWindow:
    def __init__(
        self,
        id: int = 0,
        width: int = 21,
        height: int = 10,
        x: int = 0,
        y: int = 0,
        print_method: PrintAbstract = None,
    ) -> None:
        self.id: int = id
        self.width: int = width
        self.height: int = height
        self.x: int = x
        self.y: int = y
        self.pos = {"x": 0, "y": 0}
        self.print_method = print_method or ConsolePrint()
        self.line_height = 1

    def clip_window_pos(self, pos: dict = None, inplace: bool = False):
        if pos is None:
            pos = self.pos.copy()
        if pos:
            pos["x"] = max(0, min(pos["x"], self.x + self.width - 1))
            pos["y"] = max(0, min(pos["y"], self.y + self.height - 1))
        if inplace:
            self.pos = pos
        return pos

    def get_abs_pos(self):
        pos = {"x": self.x + self.pos["x"], "y": self.y + self.pos["y"]}
        return self.clip_window_pos(pos)

    def line_cr(self):
        self.pos["x"] = 0
        self.pos["y"] += self.line_height
        self.clip_window_pos(inplace=True)

    async def print_line(self, text: str, pos: dict = None) -> None:
        if pos is not None:
            self.pos = self.clip_window_pos(pos)
        # text = f"[{self.pos["x"]}, {self.pos["y"]}] {text}"[: self.width]
        await self.print_method.print_value(text[: self.width], self.get_abs_pos())
        self.line_cr()

    async def clear(self):
        self.pos = {"x": 0, "y": 0}
        await self.clear_lines(self.height)

    async def clear_lines(self, lines: int = 1):
        for row in range(lines):
            self.pos["x"] = 0
            await self.print_line(" " * self.width)


class ConsoleWindows:
    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        gap_x: int = 4,
        gap_y: int = 1,
        windows: dict[int, ConsoleWindow] = None,
        print_method: PrintAbstract = None,
    ) -> None:
        self.windows = windows or {}
        self.x = x
        self.y = y
        self.gap_x = gap_x
        self.gap_y = gap_y
        terminal_size = os.get_terminal_size()
        self.cols = terminal_size.columns
        self.rows = terminal_size.lines
        self.print_method = print_method or ConsolePrint()
        print(f"Terminal size: {self.cols}x{self.rows}")

    def get_max_windows(self, width: int, height: int) -> tuple[int, int, int]:
        x_max_windows = self.cols // (self.x + width + self.gap_x)
        y_max_windows = self.rows // (self.y + height + self.gap_y)
        return x_max_windows * y_max_windows, x_max_windows, y_max_windows

    def add_window(
        self,
        id: int = None,
        width: int = 21,
        height: int = 10,
        print_method: PrintAbstract = None,
    ) -> int:
        if print_method is None:
            print_method = self.print_method

        if id is None:
            ids = self.windows.keys()
            if len(ids) == 0:
                id = 0
            else:
                id = max(ids) + 1

        max_windows, x_max_windows, y_max_windows = self.get_max_windows(width, height)

        if id + 1 > (max_windows):
            raise ValueError(f"Window number {id+1} is out of bounds {max_windows}.")

        window_row = id // x_max_windows
        window_col = id % x_max_windows

        x = self.x + (width + self.gap_x) * window_col
        y = self.y + (height + self.gap_y) * window_row

        window = ConsoleWindow(id, width, height, x, y, print_method)
        self.windows[id] = window
        return id

    def get_window(self, id: int) -> ConsoleWindow | None:
        return self.windows.get(id)

    def max_bottop_row(self) -> int | None:
        if len(self.windows) == 0:
            return None
        return max([window.y + window.height for window in self.windows.values()])

    async def set_cursor_to_max_pos(self):
        max_bottop_row = windows_manager.max_bottop_row()
        if max_bottop_row is not None:
            if windows_manager.print_method is not None:
                await windows_manager.print_method.print_value(
                    "", {"x": 0, "y": max_bottop_row}
                )

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, exc_type, exc_value, traceback): ...


if __name__ == "__main__":

    async def prints(windows_manager: ConsoleWindows):
        await windows_manager.print_method.clear()
        max_windows, *_ = windows_manager.get_max_windows(21, 10)
        for _ in range(0, max_windows):
            id = windows_manager.add_window()
            window = windows_manager.windows[id]
            # print("Window", window.__dict__)
            # await asyncio.sleep(2)
            # await print_method.clear()
            # await print_method.clear()
            for i in range(0, 10, 1):
                await window.print_line(f"W: {window.id}, L: {i} 01234567890123456789")
        window_clear = windows_manager.get_window(1)
        await asyncio.sleep(2)
        if window_clear:
            await window_clear.clear()
        await windows_manager.set_cursor_to_max_pos()

    # MAIN
    with ConsoleWindows() as windows_manager:  # ConsoleWindows()
        try:
            asyncio.run(prints(windows_manager))
        except Exception as e:
            print(e)
