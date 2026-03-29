import subprocess
import sys

from runners.base_runner import BaseRunner
from runners.params import RunParams


class SubprocessRunner(BaseRunner):
    """A runner that executes another python file in a subprocess with args."""

    def __init__(self, script_path: str):
        self.script_path = script_path

    def run(self, run_params: RunParams):
        """Runs the script with the given parameters.

        Args:
            run_params (RunParams): Structured parameters to pass to the script.
        """
        cmd = [sys.executable, self.script_path, *run_params.to_cli_args()]
        subprocess.run(cmd, check=True)
