import sys
import tempfile
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from runners.base_runner import BaseRunner
from runners.params import RunParams
from results_collectors.base_collector import BaseCollector

try:
    import yaml
    from grid_search.grid_search import GridSearch
except ModuleNotFoundError:
    yaml = None
    GridSearch = None


class DummyRunner(BaseRunner):
    def __init__(self):
        self.calls: list[RunParams] = []

    def run(self, run_params: RunParams):
        self.calls.append(run_params)


class DummyCollector(BaseCollector):
    def collect(self, *args, **kwargs):
        return None


@unittest.skipUnless(GridSearch is not None, "PyYAML not installed")
class GridSearchTests(unittest.TestCase):
    def test_generate_param_combinations_yields_run_params(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "grid.yaml"
            with open(config_path, "w", encoding="utf-8") as file:
                yaml.safe_dump(
                    {
                        "lr": [0.1, 0.2],
                        "recodex": [True, False],
                    },
                    file,
                )

            grid_search = GridSearch(DummyRunner(), DummyCollector(), config_path)
            combinations = list(grid_search._generate_param_combinations())

        self.assertEqual(len(combinations), 4)
        self.assertTrue(all(isinstance(item, RunParams) for item in combinations))
        self.assertIn("--lr=0.1", combinations[0].to_cli_args())

    def test_call_passes_run_params_to_runner(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "grid.yaml"
            with open(config_path, "w", encoding="utf-8") as file:
                yaml.safe_dump(
                    {
                        "epochs": [1, 2],
                        "recodex": [True],
                    },
                    file,
                )

            runner = DummyRunner()
            grid_search = GridSearch(runner, DummyCollector(), config_path)
            grid_search()

        self.assertEqual(len(runner.calls), 2)
        self.assertTrue(all(isinstance(item, RunParams) for item in runner.calls))
        cli_args = [run_params.to_cli_args() for run_params in runner.calls]
        self.assertIn(["--epochs=1", "--recodex"], cli_args)
        self.assertIn(["--epochs=2", "--recodex"], cli_args)


if __name__ == "__main__":
    unittest.main()
