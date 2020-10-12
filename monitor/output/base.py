from abc import ABC
from typing import List


class OutputDevice(ABC):
    def update_display(self, lines: List[str]):
        pass


class ConsoleOutputDevice(OutputDevice):
    def update_display(self, lines: List[str]):
        for line in lines:
            print(line)
