from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AutomationResult:
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    input: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, output: dict[str, Any], input: dict[str, Any] | None = None) -> "AutomationResult":
        return cls(success=True, output=output, input=input or {})

    @classmethod
    def fail(
        cls,
        error: str,
        input: dict[str, Any] | None = None,
        output: dict[str, Any] | None = None,
    ) -> "AutomationResult":
        return cls(success=False, error=error, input=input or {}, output=output or {})
