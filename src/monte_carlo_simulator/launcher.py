"""Start the simulator as a desktop-style application.

Double-clicking the packaged executable lands here: it picks a port, starts the
HTTP server, and opens the browser on it. The interface is served by the same
process, so there is nothing else to launch and no terminal to keep open.

The listening address is fixed to the loopback interface and deliberately not
configurable. The application has no authentication — that went with the shared
deployment — so binding anywhere else would let any device on the subnet list,
overwrite and delete the saved registers. TLS would not help: it encrypts the
connection, it does not decide who may use it.
"""

from __future__ import annotations

import argparse
import logging
import os
import socket
import threading
import time
import webbrowser
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn

from monte_carlo_simulator.resources import frontend_directory, is_frozen

DEFAULT_PORT = 8000
HOST = "127.0.0.1"
PORT_SEARCH_ATTEMPTS = 20
SERVER_READY_TIMEOUT_SECONDS = 30.0
SERVER_READY_POLL_INTERVAL_SECONDS = 0.15
SERVER_READY_REQUEST_TIMEOUT_SECONDS = 1.0

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


def server_is_ready(url: str) -> bool:
    """Return whether the packaged API is already able to answer requests."""
    try:
        with urlopen(f"{url}/api/health", timeout=SERVER_READY_REQUEST_TIMEOUT_SECONDS) as response:
            return int(response.status) == 200
    except (OSError, URLError):
        return False


def _wait_for_server_and_open_browser(
    url: str,
    *,
    timeout: float = SERVER_READY_TIMEOUT_SECONDS,
    poll_interval: float = SERVER_READY_POLL_INTERVAL_SECONDS,
) -> None:
    """Open the browser only after the health endpoint actually answers."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server_is_ready(url):
            webbrowser.open(url)
            return
        time.sleep(poll_interval)
    logger.error("Le serveur local n'a pas répondu dans le délai prévu : %s", url)


def _open_browser_when_ready(url: str) -> threading.Thread:
    """Wait for Uvicorn in the background without delaying its startup."""
    thread = threading.Thread(
        target=_wait_for_server_and_open_browser,
        args=(url,),
        name="risksim-browser-opener",
        daemon=True,
    )
    thread.start()
    return thread


def _configure_logging(frozen: bool) -> None:
    """Keep source logs useful without writing to an absent frozen console."""
    if frozen:
        logging.basicConfig(level=logging.INFO, handlers=[logging.NullHandler()])
        return
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="monte-carlo-simulator",
        description="Lance le simulateur Monte-Carlo et ouvre l'interface.",
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
    frozen = is_frozen()
    _configure_logging(frozen)
    options = build_parser().parse_args(argv)
    port = choose_port(HOST, options.port)

    if frontend_directory() is None:
        logger.warning(
            "L'interface construite est introuvable : seule l'API répondra. "
            "Depuis les sources, lancez « npm run build » dans web/ au préalable."
        )

    url = f"http://{HOST}:{port}"
    logger.info("Simulateur Monte-Carlo démarré sur %s", url)
    logger.info("L'accès est limité à cette machine ; rien ne circule sur le réseau.")
    if not options.no_browser:
        _open_browser_when_ready(url)

    uvicorn.run(
        "monte_carlo_simulator.web_api:app",
        host=HOST,
        port=port,
        # Reload rewrites the import machinery, which a frozen build cannot do.
        reload=False,
        log_level="info",
        # The frozen build deliberately has no console to receive access logs.
        log_config=None if frozen else uvicorn.config.LOGGING_CONFIG,
        access_log=not frozen,
        use_colors=not frozen,
    )


if __name__ == "__main__":  # pragma: no cover - entry point
    main()
