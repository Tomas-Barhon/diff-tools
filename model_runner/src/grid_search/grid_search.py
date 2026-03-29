from __future__ import annotations

from collections.abc import Iterable
from itertools import product

from param_search.base_param_search import (
    BaseParamSearch,
    ExecutionConfig,
    ReportingConfig,
)
from runners.params import RunParams


class GridSearch(BaseParamSearch):
    def __init__(
        self,
        runner,
        collector,
        param_grid: dict,
        execution: ExecutionConfig | None = None,
        reporting: ReportingConfig | None = None,
    ):
        super().__init__(runner, collector, execution, reporting)
        self.param_grid = param_grid

    @classmethod
    def from_experiment_config(cls, config: dict) -> "GridSearch":
        search_config = config.get("search", {})
        param_grid = search_config.get("param_grid")
        if not isinstance(param_grid, dict) or not param_grid:
            raise ValueError(
                "Missing or empty 'search.param_grid' in experiment config"
            )

        runner, collector, execution, reporting = BaseParamSearch.parse_common_config(
            config
        )
        return cls(
            runner=runner,
            collector=collector,
            param_grid=param_grid,
            execution=execution,
            reporting=reporting,
        )

    def _normalized_grid(self) -> tuple[list[str], list[list[object]]]:
        keys = list(self.param_grid.keys())
        values: list[list[object]] = []
        for key in keys:
            value = self.param_grid[key]
            if isinstance(value, str) or not isinstance(value, Iterable):
                value = [value]
            else:
                value = list(value)
            values.append(value)
        return keys, values

    def _all_run_params(self) -> tuple[list[str], list[RunParams]]:
        keys, values = self._normalized_grid()
        combinations = []
        for combination in product(*values):
            combinations.append(RunParams.from_mapping(dict(zip(keys, combination))))
        return keys, combinations

    def __call__(self) -> None:
        param_keys, run_params_list = self._all_run_params()
        if not run_params_list:
            self._console.print("[yellow]No parameter combinations to run.[/yellow]")
            return

        rows, elapsed = self._run_param_list(run_params_list, search_name="grid search")
        csv_path = self._write_results_csv(rows, param_keys)
        self._print_summary(rows, elapsed, csv_path, param_keys)
