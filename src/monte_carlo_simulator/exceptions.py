"""Custom exceptions for the simulator."""

from dataclasses import dataclass


class MonteCarloError(Exception):
    """Base exception for business errors."""


class ValidationError(MonteCarloError):
    """Raised when model or simulation input is invalid."""


@dataclass(frozen=True, slots=True)
class RiskRegisterIssue:
    """One user-facing workbook validation issue with its Excel context."""

    sheet: str
    message: str
    row: int | None = None
    item_name: str | None = None
    field: str | None = None
    value: object = None

    def __str__(self) -> str:
        context = [f"sheet={self.sheet!r}"]
        if self.row is not None:
            context.append(f"row={self.row}")
        if self.item_name:
            context.append(f"item={self.item_name!r}")
        if self.field:
            context.append(f"field={self.field!r}")
            context.append(f"value={self.value!r}")
        return f"[{', '.join(context)}] {self.message}"


class RiskRegisterValidationError(ValidationError):
    """Raised with all independently detected workbook validation issues."""

    def __init__(self, issues: list[RiskRegisterIssue] | tuple[RiskRegisterIssue, ...]) -> None:
        if not issues:
            raise ValueError("RiskRegisterValidationError requires at least one issue.")
        self.issues = tuple(issues)
        details = "\n".join(f"- {issue}" for issue in self.issues)
        super().__init__(
            f"Risk register validation failed ({len(self.issues)} issue(s)):\n{details}"
        )

    @property
    def errors(self) -> tuple[RiskRegisterIssue, ...]:
        """Backward-friendly alias for callers that use error terminology."""
        return self.issues
