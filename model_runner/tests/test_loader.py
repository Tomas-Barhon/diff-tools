import sys
import tempfile
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from grid_search.grid_search import GridSearch
from optuna_search.optuna_search import OptunaSearch
from param_search.loader import load_param_search_from_config


class LoaderTests(unittest.TestCase):
    def test_loads_grid_search_backend(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "exp.yaml"
            path.write_text(
                "\n".join(
                    [
                        "runner:",
                        "  script_path: ./script.py",
                        "collector:",
                        "  regex: 'score: ([-0-9.]+)'",
                        "search:",
                        "  backend: grid",
                        "  param_grid:",
                        "    x: [1, 2]",
                    ]
                ),
                encoding="utf-8",
            )
            search = load_param_search_from_config(path)
        self.assertIsInstance(search, GridSearch)

    def test_loads_optuna_search_backend(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "exp.yaml"
            path.write_text(
                "\n".join(
                    [
                        "runner:",
                        "  script_path: ./script.py",
                        "collector:",
                        "  regex: 'score: ([-0-9.]+)'",
                        "search:",
                        "  backend: optuna",
                        "  n_trials: 2",
                        "  space:",
                        "    x:",
                        "      type: int",
                        "      low: 1",
                        "      high: 2",
                    ]
                ),
                encoding="utf-8",
            )
            search = load_param_search_from_config(path)
        self.assertIsInstance(search, OptunaSearch)


if __name__ == "__main__":
    unittest.main()
