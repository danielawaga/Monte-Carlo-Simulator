"""Tests for password hashing."""

from __future__ import annotations

import pytest

from monte_carlo_simulator.storage import passwords


def test_the_same_password_never_produces_the_same_hash() -> None:
    """Distinct salts are what stop one leaked hash from unlocking every reuse."""
    first = passwords.hash_password("motdepasse-solide")
    second = passwords.hash_password("motdepasse-solide")

    assert first != second
    assert passwords.verify_password("motdepasse-solide", first)
    assert passwords.verify_password("motdepasse-solide", second)


def test_a_wrong_password_is_refused() -> None:
    stored = passwords.hash_password("motdepasse-solide")

    assert passwords.verify_password("motdepasse-solid", stored) is False
    assert passwords.verify_password("", stored) is False


def test_the_hash_describes_its_own_parameters() -> None:
    algorithm, n, r, p, salt, key = passwords.hash_password("motdepasse-solide").split("$")

    assert algorithm == "scrypt"
    assert (int(n), int(r), int(p)) == (
        passwords.SCRYPT_N,
        passwords.SCRYPT_R,
        passwords.SCRYPT_P,
    )
    assert len(bytes.fromhex(salt)) == passwords.SALT_BYTES
    assert len(bytes.fromhex(key)) == passwords.KEY_BYTES


@pytest.mark.parametrize(
    "stored",
    ["", "pas-un-hash", "scrypt$trop$peu$champs", "argon2$1$2$3$aa$bb", "scrypt$x$8$1$aa$bb"],
)
def test_a_malformed_hash_never_authenticates(stored: str) -> None:
    assert passwords.verify_password("motdepasse-solide", stored) is False


def test_short_passwords_are_reported_and_long_ones_accepted() -> None:
    assert passwords.password_issue("court") is not None
    assert passwords.password_issue("a" * passwords.MINIMUM_PASSWORD_LENGTH) is None


def test_unicode_passwords_round_trip() -> None:
    secret = "château-fort-éàü-日本"
    assert passwords.verify_password(secret, passwords.hash_password(secret))
