"""Start the simulator as a desktop-style application.

Double-clicking the packaged executable lands here: it picks a port, starts the
HTTP server, and opens the browser on it. The interface is served by the same
process, so there is nothing else to launch and no terminal to keep open.
"""

from __future__ import annotations

import argparse
import logging
import os
import socket
import threading
import webbrowser

import uvicorn

from monte_carlo_simulator.resources import frontend_directory, is_frozen

DEFAULT_PORT = 8000
DEFAULT_HOST = "127.0.0.1"
PORT_SEARCH_ATTEMPTS = 20

logger = logging.getLogger(__name__)


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def choose_port(host: str, preferred: int = DEFAULT_PORT) -> int:
    """Return the first free port at or after ``preferred``.

    A second launch, or anything else already holding 8000, should not end in a
    stack trace on a machine nobody is watching a terminal on.
    """
    for candidate in range(preferred, preferred + PORT_SEARCH_ATTEMPTS):
        if port_is_free(host, candidate):
            return candidate
    raise SystemExit(
        f"Aucun port libre entre {preferred} et {preferred + PORT_SEARCH_ATTEMPTS - 1}."
    )


def _open_browser_later(url: str, delay: float = 1.5) -> None:
    """Open the browser once the server has had time to start listening."""
    threading.Timer(delay, lambda: webbrowser.open(url)).start()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="monte-carlo-simulator",
        description="Lance le simulateur Monte-Carlo et ouvre l'interface.",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCS_HOST", DEFAULT_HOST),
        help=(
            "Adresse d'écoute. 127.0.0.1 (défaut) restreint l'accès à cette machine ; "
            "0.0.0.0 expose le service à tout le réseau local."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCS_PORT", DEFAULT_PORT)),
        help=f"Port souhaité, {DEFAULT_PORT} par défaut. Le premier port libre suivant est pris.",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Ne pas ouvrir le navigateur au démarrage."
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    options = build_parser().parse_args(argv)
    port = choose_port(options.host, options.port)

    if frontend_directory() is None:
        logger.warning(
            "L'interface construite est introuvable : seule l'API répondra. "
            "Depuis les sources, lancez « npm run build » dans web/ au préalable."
        )

    # Reaching a server bound to 127.0.0.1 needs that same address in the URL,
    # while 0.0.0.0 is a bind address and not something a browser can open.
    reachable = "127.0.0.1" if options.host in ("0.0.0.0", "") else options.host
    url = f"http://{reachable}:{port}"
    logger.info("Simulateur Monte-Carlo démarré sur %s", url)
    if options.host == "0.0.0.0":
        logger.warning(
            "Écoute sur toutes les interfaces : le service est joignable par tout le "
            "réseau, wifi invité compris si le réseau est plat."
        )
    if not options.no_browser:
        _open_browser_later(url)

    uvicorn.run(
        "monte_carlo_simulator.web_api:app",
        host=options.host,
        port=port,
        # Reload rewrites the import machinery, which a frozen build cannot do.
        reload=False,
        log_level="info",
        # A packaged build has no colour-capable terminal behind it.
        use_colors=not is_frozen(),
    )


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
