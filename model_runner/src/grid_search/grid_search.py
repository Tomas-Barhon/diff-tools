from argparse import ArgumentParser
from pathlib import Path
import yaml
from itertools import product
from runners.base_runner import BaseRunner
from runners.params import RunParams
from results_collectors.base_collector import BaseCollector


class GridSearch:
    def __init__(
        self, runner: BaseRunner, collector: BaseCollector, param_grid_path: str | Path
    ):
        self.param_grid = self._load_param_grid(param_grid_path)
        self.runner = runner
        self.collector = collector

    def _load_param_grid(self, param_grid_path: str | Path) -> dict:
        with open(param_grid_path, "r") as f:
            param_grid = yaml.safe_load(f)
        return param_grid

    def _generate_param_combinations(self):
        keys = self.param_grid.keys()
        values = [self.param_grid[key] for key in keys]
        for combination in product(*values):
            yield RunParams.from_mapping(dict(zip(keys, combination)))

    def __call__(self):
        for param_combination in self._generate_param_combinations():
            self.runner.run(param_combination)


if __name__ == "__main__":
    parser = ArgumentParser(description="Run grid search with specified config.")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the YAML file containing the parameter grid.",
    )
    args = parser.parse_args()

    # Example usage with dummy runner and collector
    runner = BaseRunner()  # Replace with actual runner implementation
    collector = BaseCollector()  # Replace with actual collector implementation
    grid_search = GridSearch(runner, collector, args.config)
    grid_search()
