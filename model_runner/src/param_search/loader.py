from __future__ import annotations

from pathlib import Path

import yaml

from grid_search.grid_search import GridSearch
from optuna_search.optuna_search import OptunaSearch


def load_param_search_from_config(experiment_config_path: str | Path):
    with open(experiment_config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    search_config = config.get("search", {})
    backend = str(search_config.get("backend", "grid"))

    if backend == "grid":
        return GridSearch.from_experiment_config(config)
    if backend == "optuna":
        return OptunaSearch.from_experiment_config(config)

    raise ValueError(
        f"Unsupported search backend '{backend}', expected 'grid' or 'optuna'"
    )
