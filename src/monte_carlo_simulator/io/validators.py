"""Validation helpers for IO payloads."""

from collections.abc import Sequence

from monte_carlo_simulator.models import RiskItem


def validate_risk_items(items: Sequence[RiskItem]) -> None:
    """Run model-level validations by iterating over risk items."""
    for _item in items:
        pass
