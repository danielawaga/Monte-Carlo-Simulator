"""Shared-secret access gate protecting the hosted interfaces.

The platform keeps no server-side state: there is no user directory to
authenticate against, and every request works in a temporary directory that is
destroyed once the response is sent. What this module provides is therefore not
a user system but a single shared secret, read from the environment, that the
HTTP API checks before doing any work.

When the secret is not configured the gate stays open, so local development and
the test suite keep working exactly as before.
"""

from __future__ import annotations

import hmac
import logging
import os

logger = logging.getLogger(__name__)

ACCESS_KEY_ENV = "MCS_ACCESS_KEY"
ACCESS_KEY_HEADER = "X-Access-Key"
MINIMUM_KEY_LENGTH = 12


def configured_access_key() -> str | None:
    """Return the shared secret configured for this deployment, if any."""
    key = os.environ.get(ACCESS_KEY_ENV, "").strip()
    return key or None


def gate_is_enabled() -> bool:
    """Tell whether requests must carry the shared secret."""
    return configured_access_key() is not None


def verify_access_key(candidate: str | None) -> bool:
    """Compare a submitted secret with the configured one in constant time."""
    expected = configured_access_key()
    if expected is None:
        return True
    if not candidate:
        return False
    return hmac.compare_digest(candidate.strip(), expected)


def log_gate_configuration() -> None:
    """Report the gate state at startup so a misconfigured deployment is visible."""
    key = configured_access_key()
    if key is None:
        logger.warning(
            "%s n'est pas défini : l'accès à la plateforme est ouvert. "
            "Définissez cette variable avant tout déploiement accessible depuis Internet.",
            ACCESS_KEY_ENV,
        )
        return
    if len(key) < MINIMUM_KEY_LENGTH:
        logger.warning(
            "%s est plus court que %d caractères : choisissez un secret plus long.",
            ACCESS_KEY_ENV,
            MINIMUM_KEY_LENGTH,
        )
