import sys
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from runners.params import RunParams


class RunParamsTests(unittest.TestCase):
    def test_from_mapping_copies_input(self):
        source = {"epochs": 10}

        run_params = RunParams.from_mapping(source)
        source["epochs"] = 20

        self.assertEqual(run_params.params["epochs"], 10)

    def test_to_cli_args_handles_values_and_flags(self):
        run_params = RunParams.from_mapping(
            {
                "epochs": 10,
                "model": "baseline",
                "recodex": True,
                "dry_run": None,
                "cache": False,
            }
        )

        self.assertEqual(
            run_params.to_cli_args(),
            ["--epochs=10", "--model=baseline", "--recodex", "--dry_run"],
        )

    def test_to_cli_args_empty_mapping(self):
        run_params = RunParams()

        self.assertEqual(run_params.to_cli_args(), [])


if __name__ == "__main__":
    unittest.main()
