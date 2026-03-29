from abc import ABC, abstractmethod


class BaseCollector(ABC):
    @abstractmethod
    def collect(self, output: str) -> list[str]:
        pass
