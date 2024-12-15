from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(f"BLEScanner.{__name__}")


class PrintAbstract(ABC):
    @abstractmethod
    def print_value(self, text: str, pos: dict = None) -> None: ...

    @abstractmethod
    def clear(self) -> None: ...

    def clear_lines(self, lines: int = 1): ...


class ConsolePrint(PrintAbstract):
    def print_value(self, text: str, pos: dict = None) -> None:
        if pos is not None:
            print_text = f'\033[{str(pos["y"])};{str(pos["x"])}H{text}'
        else:
            print_text = text

        print(print_text)

    def clear(self):
        print("\033c\033[3J")

    def clear_lines(self, lines: int = 1):
        for _ in range(lines):
            print("\033[K")
