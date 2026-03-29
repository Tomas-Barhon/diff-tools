import csv
import sys
import tempfile
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from grid_search.grid_search import GridSearch
from param_search.base_param_search import ExecutionConfig, ReportingConfig
from results_collectors.base_collector import BaseCollector
from runners.base_runner import BaseRunner
from runners.params import RunParams
from runners.run_result import RunResult


class DummyRunner(BaseRunner):
    def __init__(self):
        self.calls: list[RunParams] = []

    def run(self, run_params: RunParams) -> RunResult:
        self.calls.append(run_params)
        value = run_params.params.get("value", 0)
        return RunResult(
            success=True,
            stdout=f"score: {value}\n",
            stderr="",
            returncode=0,
            duration_seconds=0.01,
        )


class DummyCollector(BaseCollector):
    def collect(self, output: str) -> list[str]:
        for line in output.splitlines():
            if line.startswith("score: "):
                return [line.split(": ", maxsplit=1)[1]]
        return []


class GridSearchTests(unittest.TestCase):
    def test_scalar_values_are_wrapped(self):
        search = GridSearch(
            runner=DummyRunner(),
            collector=DummyCollector(),
            param_grid={"lr": 0.1, "seed": [1, 2]},
        )
        _, combinations = search._all_run_params()

        self.assertEqual(len(combinations), 2)
        self.assertEqual(combinations[0].params["lr"], 0.1)

    def test_call_runs_and_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "results.csv"
            search = GridSearch(
                runner=DummyRunner(),
                collector=DummyCollector(),
                param_grid={"value": [3, 1, 2]},
                execution=ExecutionConfig(jobs=1, continue_on_failure=True),
                reporting=ReportingConfig(
                    results_csv=str(csv_path),
                    top_k=2,
                    metric_name="score",
                    metric_mode="max",
                    show_progress=False,
                    show_run_logs=False,
                ),
            )

            search()

            with open(csv_path, "r", encoding="utf-8", newline="") as file:
                rows = list(csv.reader(file))

        self.assertEqual(rows[0], ["value", "score"])
        self.assertEqual(len(rows), 4)

    def test_from_experiment_config_defaults_jobs_to_one(self):
        config = {
            "runner": {"script_path": "./script.py"},
            "collector": {"regex": "score: ([-0-9.]+)"},
            "search": {"backend": "grid", "param_grid": {"value": [1, 2]}},
        }
        search = GridSearch.from_experiment_config(config)

        self.assertEqual(search.execution.jobs, 1)
        self.assertEqual(search.reporting.metric_mode, "max")


if __name__ == "__main__":
    unittest.main()
