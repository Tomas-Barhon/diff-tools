from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from results_collectors.base_collector import BaseCollector
from results_collectors.regex_collector import RegexCollector
from runners.base_runner import BaseRunner
from runners.params import RunParams
from runners.subprocess_runner import SubprocessRunner


@dataclass(slots=True)
class ExecutionConfig:
    jobs: int = 1
    continue_on_failure: bool = True


@dataclass(slots=True)
class ReportingConfig:
    results_csv: str = "results.csv"
    top_k: int = 5
    metric_name: str = "result"
    metric_mode: str = "max"
    show_progress: bool = True
    show_run_logs: bool = True


class BaseParamSearch(ABC):
    def __init__(
        self,
        runner: BaseRunner,
        collector: BaseCollector,
        execution: ExecutionConfig | None = None,
        reporting: ReportingConfig | None = None,
    ) -> None:
        self.runner = runner
        self.collector = collector
        self.execution = execution or ExecutionConfig()
        self.reporting = reporting or ReportingConfig()
        self._console = Console()

    @staticmethod
    def parse_common_config(
        config: dict,
    ) -> tuple[BaseRunner, BaseCollector, ExecutionConfig, ReportingConfig]:
        runner_config = config.get("runner", {})
        collector_config = config.get("collector", {})
        execution_config = config.get("execution", {})
        reporting_config = config.get("reporting", {})

        script_path = runner_config.get("script_path")
        if not script_path:
            raise ValueError("Missing 'runner.script_path' in experiment config")

        regex = collector_config.get("regex")
        if not regex:
            raise ValueError("Missing 'collector.regex' in experiment config")

        jobs = int(execution_config.get("jobs", 1))
        if jobs < 1:
            raise ValueError("'execution.jobs' must be >= 1")

        metric_mode = str(reporting_config.get("metric_mode", "max"))
        if metric_mode not in {"max", "min"}:
            raise ValueError("'reporting.metric_mode' must be 'max' or 'min'")

        execution = ExecutionConfig(
            jobs=jobs,
            continue_on_failure=bool(execution_config.get("continue_on_failure", True)),
        )
        reporting = ReportingConfig(
            results_csv=str(reporting_config.get("results_csv", "results.csv")),
            top_k=int(reporting_config.get("top_k", 5)),
            metric_name=str(reporting_config.get("metric_name", "result")),
            metric_mode=metric_mode,
            show_progress=bool(reporting_config.get("show_progress", True)),
            show_run_logs=bool(reporting_config.get("show_run_logs", True)),
        )

        return (
            SubprocessRunner(script_path),
            RegexCollector(regex),
            execution,
            reporting,
        )

    @staticmethod
    def _to_float(value: str) -> float | None:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _execute_one(
        self, run_index: int, total_runs: int, run_params: RunParams
    ) -> dict:
        run_result = self.runner.run(run_params)
        merged_output = (
            f"{run_result.stdout}\n{run_result.stderr}"
            if run_result.stderr
            else run_result.stdout
        )
        collected = self.collector.collect(merged_output)
        result = collected[-1] if collected else "FAILED"

        is_failed = (not run_result.success) or result == "FAILED"
        if is_failed and not self.execution.continue_on_failure:
            raise RuntimeError(run_result.error_message or f"Run {run_index} failed")

        return {
            "index": run_index,
            "total_runs": total_runs,
            "params": run_params.params,
            "result": result,
            "success": run_result.success and result != "FAILED",
            "duration_seconds": run_result.duration_seconds,
            "returncode": run_result.returncode,
        }

    def _log_row(self, row: dict) -> None:
        if not self.reporting.show_run_logs:
            return
        status = "OK" if row["success"] else "FAILED"
        params_text = " ".join(f"{key}={value}" for key, value in row["params"].items())
        self._console.print(
            f"[{'green' if status == 'OK' else 'red'}]"
            f"[{status}] run {row['index']}/{row['total_runs']}"
            f" result={row['result']}"
            f" time={row['duration_seconds']:.2f}s"
            f" params=({params_text})"
            f"[/]"
        )

    def _run_param_list(
        self, run_params_list: list[RunParams], search_name: str
    ) -> tuple[list[dict], float]:
        total_runs = len(run_params_list)
        self._console.print(
            f"[bold]Starting {search_name}[/bold] with {total_runs} runs | jobs={self.execution.jobs} | metric_mode={self.reporting.metric_mode}"
        )

        started = perf_counter()
        rows_by_index: dict[int, dict] = {}

        progress_columns = [
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ]

        with Progress(
            *progress_columns,
            console=self._console,
            disable=not self.reporting.show_progress,
        ) as progress:
            task = progress.add_task("Runs", total=total_runs)
            with ThreadPoolExecutor(max_workers=self.execution.jobs) as executor:
                future_to_index = {
                    executor.submit(
                        self._execute_one, index + 1, total_runs, params
                    ): index
                    for index, params in enumerate(run_params_list)
                }

                for future in as_completed(future_to_index):
                    original_index = future_to_index[future]
                    row = future.result()
                    rows_by_index[original_index] = row
                    self._log_row(row)
                    progress.advance(task, 1)

        elapsed = perf_counter() - started
        rows = [rows_by_index[index] for index in range(total_runs)]
        return rows, elapsed

    def _write_results_csv(self, rows: list[dict], param_keys: list[str]) -> Path:
        csv_path = Path(self.reporting.results_csv)
        with open(csv_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([*param_keys, self.reporting.metric_name])
            for row in rows:
                writer.writerow(
                    [row["params"].get(key) for key in param_keys] + [row["result"]]
                )
        return csv_path

    def _print_summary(
        self, rows: list[dict], elapsed: float, csv_path: Path, param_keys: list[str]
    ) -> None:
        total_runs = len(rows)
        failed_count = sum(1 for row in rows if not row["success"])
        success_count = total_runs - failed_count

        self._console.print(
            f"[bold]Finished[/bold] in {elapsed:.2f}s | success={success_count} | failed={failed_count} | csv={csv_path}"
        )

        numeric_rows: list[tuple[float, dict]] = []
        for row in rows:
            numeric_result = self._to_float(row["result"])
            if numeric_result is None:
                continue
            numeric_rows.append((numeric_result, row))

        if not numeric_rows:
            self._console.print(
                "[yellow]No numeric results available for top-k summary.[/yellow]"
            )
            return

        reverse = self.reporting.metric_mode == "max"
        numeric_rows.sort(key=lambda item: item[0], reverse=reverse)
        top_rows = numeric_rows[: max(self.reporting.top_k, 0)]

        table = Table(
            title=f"Top {len(top_rows)} Results ({self.reporting.metric_mode})"
        )
        table.add_column("Rank", justify="right")
        for key in param_keys:
            table.add_column(key)
        table.add_column(self.reporting.metric_name, justify="right")

        for rank, (numeric_result, row) in enumerate(top_rows, start=1):
            table.add_row(
                str(rank),
                *[str(row["params"].get(key)) for key in param_keys],
                f"{numeric_result:.6g}",
            )
        self._console.print(table)

    @abstractmethod
    def __call__(self) -> None:
        pass
