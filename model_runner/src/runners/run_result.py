from dataclasses import dataclass


@dataclass(slots=True)
class RunResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int
    duration_seconds: float
    error_message: str | None = None
