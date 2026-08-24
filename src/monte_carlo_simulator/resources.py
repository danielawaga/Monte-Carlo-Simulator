"""Locate bundled files, whether running from the source tree or an executable.

A PyInstaller build unpacks itself into a temporary directory and points
``sys._MEIPASS`` at it, so paths computed from ``__file__`` — which work fine in
the repository — resolve to nothing there. Everything the application reads at
runtime goes through here instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Two levels up from this file is the package root's parent, i.e. ``src/``;
# three levels up is the repository. Only meaningful outside a bundle.
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def is_frozen() -> bool:
    """Tell whether the application is running from a packaged executable."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def resource_root() -> Path:
    """Return the directory bundled data files live under."""
    if is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]  # noqa: SLF001
    return _REPOSITORY_ROOT


def resource_path(*parts: str) -> Path:
    """Resolve a bundled file, e.g. ``resource_path("data", "templates", "x.xlsx")``."""
    return resource_root().joinpath(*parts)


def frontend_directory() -> Path | None:
    """Return the built React interface, when it is available to be served.

    A packaged executable always carries it. From a source checkout it exists
    only after ``npm run build``, and its absence is normal during development —
    the Vite dev server serves the interface then, and the API only answers
    ``/api`` calls.
    """
    candidate = resource_path("web", "dist")
    return candidate if (candidate / "index.html").is_file() else None
