import subprocess
import sys
import time

from runners.base_runner import BaseRunner
from runners.params import RunParams
from runners.run_result import RunResult


class SubprocessRunner(BaseRunner):
    """A runner that executes another python file in a subprocess with args."""

    def __init__(self, script_path: str):
        self.script_path = script_path

    def run(self, run_params: RunParams) -> RunResult:
        """Runs the script with the given parameters.

        Args:
            run_params (RunParams): Structured parameters to pass to the script.
        """
        cmd = [sys.executable, self.script_path, *run_params.to_cli_args()]
        started = time.perf_counter()
        try:
            completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return RunResult(
                success=True,
                stdout=completed.stdout,
                stderr=completed.stderr,
                returncode=completed.returncode,
                duration_seconds=time.perf_counter() - started,
            )
        except subprocess.CalledProcessError as error:
            return RunResult(
                success=False,
                stdout=error.stdout or "",
                stderr=error.stderr or "",
                returncode=error.returncode,
                duration_seconds=time.perf_counter() - started,
                error_message=str(error),
            )
