import csv
import sys
import tempfile
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from optuna_search.optuna_search import OptunaSearch


class OptunaSearchTests(unittest.TestCase):
    def test_runs_trials_and_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "optuna_results.csv"
            config = {
                "runner": {"script_path": "./fake.py"},
                "collector": {"regex": "score: ([-0-9.]+)"},
                "search": {
                    "backend": "optuna",
                    "n_trials": 4,
                    "space": {
                        "value": {
                            "type": "categorical",
                            "choices": [1, 2],
                        }
                    },
                },
                "reporting": {
                    "results_csv": str(csv_path),
                    "metric_name": "score",
                    "show_progress": False,
                    "show_run_logs": False,
                },
            }

            search = OptunaSearch.from_experiment_config(config)

            def fake_run(run_params):
                value = run_params.params["value"]
                from runners.run_result import RunResult

                return RunResult(
                    success=True,
                    stdout=f"score: {value}\n",
                    stderr="",
                    returncode=0,
                    duration_seconds=0.01,
                )

            search.runner.run = fake_run
            search()

            with open(csv_path, "r", encoding="utf-8", newline="") as file:
                rows = list(csv.reader(file))

        self.assertEqual(rows[0], ["value", "score"])
        self.assertEqual(len(rows), 5)


if __name__ == "__main__":
    unittest.main()
