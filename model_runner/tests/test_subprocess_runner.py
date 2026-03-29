import sys
import unittest
from pathlib import Path
from unittest.mock import patch

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from runners.params import RunParams
from runners.subprocess_runner import SubprocessRunner


class SubprocessRunnerTests(unittest.TestCase):
    @patch("runners.subprocess_runner.subprocess.run")
    def test_run_builds_command_with_serialized_params(self, mock_run):
        runner = SubprocessRunner("script.py")
        run_params = RunParams.from_mapping(
            {
                "epochs": 10,
                "recodex": True,
                "skip": False,
            }
        )

        runner.run(run_params)

        mock_run.assert_called_once_with(
            [sys.executable, "script.py", "--epochs=10", "--recodex"],
            check=True,
        )


if __name__ == "__main__":
    unittest.main()
