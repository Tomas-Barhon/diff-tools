from __future__ import annotations

from dataclasses import dataclass

import optuna

from param_search.base_param_search import BaseParamSearch
from runners.params import RunParams


@dataclass(slots=True)
class OptunaStorageConfig:
    url: str | None = None
    study_name: str | None = None
    load_if_exists: bool = True


class OptunaSearch(BaseParamSearch):
    def __init__(
        self,
        runner,
        collector,
        search_space: dict,
        n_trials: int,
        storage: OptunaStorageConfig,
        execution=None,
        reporting=None,
    ):
        super().__init__(runner, collector, execution, reporting)
        self.search_space = search_space
        self.n_trials = n_trials
        self.storage = storage

    @classmethod
    def from_experiment_config(cls, config: dict) -> "OptunaSearch":
        search_config = config.get("search", {})
        search_space = search_config.get("space")
        if not isinstance(search_space, dict) or not search_space:
            raise ValueError("Missing or empty 'search.space' for optuna backend")

        n_trials = int(search_config.get("n_trials", 20))
        if n_trials < 1:
            raise ValueError("'search.n_trials' must be >= 1")

        storage_cfg = search_config.get("storage", {})
        storage = OptunaStorageConfig(
            url=storage_cfg.get("url"),
            study_name=storage_cfg.get("study_name"),
            load_if_exists=bool(storage_cfg.get("load_if_exists", True)),
        )

        runner, collector, execution, reporting = BaseParamSearch.parse_common_config(
            config
        )
        return cls(
            runner=runner,
            collector=collector,
            search_space=search_space,
            n_trials=n_trials,
            storage=storage,
            execution=execution,
            reporting=reporting,
        )

    def _suggest_params(self, trial: optuna.Trial) -> dict[str, object]:
        params: dict[str, object] = {}
        for name, spec in self.search_space.items():
            if not isinstance(spec, dict):
                params[name] = spec
                continue

            kind = spec.get("type")
            if kind == "categorical":
                choices = spec.get("choices")
                if not isinstance(choices, list) or not choices:
                    raise ValueError(
                        f"Optuna param '{name}' categorical requires non-empty 'choices'"
                    )
                params[name] = trial.suggest_categorical(name, choices)
            elif kind == "int":
                params[name] = trial.suggest_int(
                    name,
                    int(spec["low"]),
                    int(spec["high"]),
                    step=int(spec.get("step", 1)),
                    log=bool(spec.get("log", False)),
                )
            elif kind == "float":
                params[name] = trial.suggest_float(
                    name,
                    float(spec["low"]),
                    float(spec["high"]),
                    step=(None if "step" not in spec else float(spec["step"])),
                    log=bool(spec.get("log", False)),
                )
            else:
                raise ValueError(
                    f"Optuna param '{name}' has unsupported type '{kind}', expected categorical/int/float"
                )
        return params

    def __call__(self) -> None:
        direction = "maximize" if self.reporting.metric_mode == "max" else "minimize"
        study = optuna.create_study(
            direction=direction,
            study_name=self.storage.study_name,
            storage=self.storage.url,
            load_if_exists=self.storage.load_if_exists,
        )

        run_params_list: list[RunParams] = []
        asked_trial_numbers: list[int] = []
        for _ in range(self.n_trials):
            trial = study.ask()
            asked_trial_numbers.append(trial.number)
            params = self._suggest_params(trial)
            run_params_list.append(RunParams.from_mapping(params))

        rows, elapsed = self._run_param_list(
            run_params_list, search_name="optuna search"
        )

        for row in rows:
            value = self._to_float(row["result"])
            trial_number = asked_trial_numbers[row["index"] - 1]
            if value is None:
                study.tell(trial_number, state=optuna.trial.TrialState.FAIL)
            else:
                study.tell(trial_number, value)

        param_keys = list(self.search_space.keys())
        csv_path = self._write_results_csv(rows, param_keys)
        self._print_summary(rows, elapsed, csv_path, param_keys)
