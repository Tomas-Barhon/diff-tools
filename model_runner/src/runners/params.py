from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(slots=True)
class RunParams:
    """Structured runner parameters that can be serialized to CLI arguments."""

    params: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, params: Mapping[str, object]) -> "RunParams":
        return cls(params=dict(params))

    def to_cli_args(self) -> list[str]:
        args: list[str] = []
        for key, value in self.params.items():
            if value is False:
                continue
            if value is None or value is True:
                args.append(f"--{key}")
                continue
            args.append(f"--{key}={value}")
        return args
