from abc import ABC, abstractmethod

from runners.params import RunParams


class BaseRunner(ABC):
    @abstractmethod
    def run(self, run_params: RunParams):
        pass
