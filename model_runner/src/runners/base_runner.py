from abc import ABC, abstractmethod

from runners.params import RunParams
from runners.run_result import RunResult


class BaseRunner(ABC):
    @abstractmethod
    def run(self, run_params: RunParams) -> RunResult:
        pass
