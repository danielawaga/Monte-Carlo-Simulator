"""Password hashing for the local account system.

``hashlib.scrypt`` is used rather than argon2id, which would otherwise be the
default recommendation. The reason is deployment: the application is meant to
ship as a double-clickable executable, and scrypt ships with CPython while
argon2 needs a compiled extension that has to be bundled and kept in step with
the interpreter. scrypt is a memory-hard KDF designed for exactly this job, so
the trade is a small step down in fashion for a real gain in packaging.

Parameters follow the interactive-login profile: n=2^15, r=8, p=1, which costs
roughly 32 MB of memory per verification. That is deliberate — it is what makes
an offline attack on a stolen database expensive.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32
ALGORITHM = "scrypt"
MINIMUM_PASSWORD_LENGTH = 10


def hash_password(password: str) -> str:
    """Return a self-describing hash: algorithm, parameters, salt and key."""
    salt = secrets.token_bytes(SALT_BYTES)
    key = _derive(password, salt)
    return f"{ALGORITHM}${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash, in constant time."""
    try:
        algorithm, raw_n, raw_r, raw_p, raw_salt, raw_key = stored.split("$")
        if algorithm != ALGORITHM:
            return False
        salt = bytes.fromhex(raw_salt)
        expected = bytes.fromhex(raw_key)
        candidate = _derive(
            password,
            salt,
            n=int(raw_n),
            r=int(raw_r),
            p=int(raw_p),
            length=len(expected),
        )
    except (ValueError, TypeError):
        # A malformed or truncated hash can never authenticate anyone.
        return False
    return hmac.compare_digest(candidate, expected)


def _derive(
    password: str,
    salt: bytes,
    *,
    n: int = SCRYPT_N,
    r: int = SCRYPT_R,
    p: int = SCRYPT_P,
    length: int = KEY_BYTES,
) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=length,
        maxmem=(128 * n * r) * 2,
    )


def password_issue(password: str) -> str | None:
    """Return why a password is unacceptable, or ``None`` when it is fine.

    The rule is length only. Composition rules (a digit, a capital, a symbol)
    push people towards predictable substitutions without adding real strength.
    """
    if len(password) < MINIMUM_PASSWORD_LENGTH:
        return f"Le mot de passe doit contenir au moins {MINIMUM_PASSWORD_LENGTH} caractères."
    return None
