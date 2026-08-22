"""Unit tests for the shared-secret access gate helpers."""

import pytest

from monte_carlo_simulator.access import (
    ACCESS_KEY_ENV,
    configured_access_key,
    gate_is_enabled,
    verify_access_key,
)


def test_gate_is_disabled_when_no_key_is_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ACCESS_KEY_ENV, raising=False)
    assert configured_access_key() is None
    assert gate_is_enabled() is False


def test_blank_key_counts_as_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ACCESS_KEY_ENV, "   ")
    assert configured_access_key() is None
    assert gate_is_enabled() is False


def test_open_gate_accepts_any_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ACCESS_KEY_ENV, raising=False)
    assert verify_access_key(None) is True
    assert verify_access_key("n’importe quoi") is True


def test_configured_gate_only_accepts_the_shared_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ACCESS_KEY_ENV, "cle-partagee-de-test")
    assert gate_is_enabled() is True
    assert verify_access_key("cle-partagee-de-test") is True
    assert verify_access_key("  cle-partagee-de-test  ") is True
    assert verify_access_key("cle-partagee-de-tes") is False
    assert verify_access_key("") is False
    assert verify_access_key(None) is False
