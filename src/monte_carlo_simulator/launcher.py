"""Start the simulator as a portable local application.

Double-clicking the packaged executable lands here: it keeps a diagnostic
terminal visible, picks a port, starts the HTTP server, and opens the browser
only once the application is ready. The same terminal provides a predictable
shutdown path through Ctrl+C or the commands ``exit``, ``quit`` and ``q``.

The listening address is fixed to the loopback interface and deliberately not
configurable. The application has no authentication — that went with the shared
deployment — so binding anywhere else would let any device on the subnet list,
overwrite and delete the saved registers. TLS would not help: it encrypts the
connection, it does not decide who may use it.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import logging
import os
import socket
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from typing import Protocol, TextIO
from urllib.error import URLError
from urllib.request import urlopen

from monte_carlo_simulator.resources import frontend_directory, is_frozen

DEFAULT_PORT = 8000
HOST = "127.0.0.1"
PORT_SEARCH_ATTEMPTS = 20
SERVER_READY_TIMEOUT_SECONDS = 30.0
SERVER_READY_POLL_INTERVAL_SECONDS = 0.15
SERVER_READY_REQUEST_TIMEOUT_SECONDS = 1.0
EXISTING_INSTANCE_TIMEOUT_SECONDS = 30.0
SINGLE_INSTANCE_MUTEX_NAME = r"Local\RiskSimMonteCarloSimulator"
WINDOWS_ERROR_ALREADY_EXISTS = 183
STOP_COMMANDS = frozenset({"exit", "quit", "q"})

logger = logging.getLogger(__name__)


class ShutdownServer(Protocol):
    should_exit: bool


def _startup_error_log_path() -> Path:
    """Keep startup diagnostics beside the portable launchers when possible."""
    if is_frozen():
        return Path(sys.executable).resolve().with_name("RiskSim-erreur-demarrage.txt")
    return Path.cwd() / "RiskSim-erreur-demarrage.txt"


def _report_startup_failure() -> None:
    """Persist a traceback and make a frozen startup failure visible."""
    details = traceback.format_exc()
    log_path = _startup_error_log_path()
    try:
        log_path.write_text(details, encoding="utf-8")
        log_hint = f"\n\nLe diagnostic complet a été enregistré dans :\n{log_path}"
    except OSError:
        log_hint = "\n\nLe fichier de diagnostic n'a pas pu être écrit."

    print("\nRiskSim n'a pas pu démarrer.\n", file=sys.stderr)
    print(details, file=sys.stderr)
    print(log_hint, file=sys.stderr)
    if is_frozen() and getattr(sys.stdin, "isatty", lambda: False)():
        try:
            input("\nAppuyez sur Entrée pour fermer cette fenêtre...")
        except (EOFError, KeyboardInterrupt):
            pass


def _acquire_single_instance_mutex() -> tuple[int | None, bool]:
    """Create a Windows named mutex and report whether it already existed.

    Keeping the returned handle open for the lifetime of the server prevents
    two near-simultaneous double-clicks from both selecting port 8000.
    """
    if not is_frozen() or os.name != "nt":
        return None, False

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_mutex = kernel32.CreateMutexW
    create_mutex.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
    create_mutex.restype = ctypes.c_void_p
    handle = create_mutex(None, False, SINGLE_INSTANCE_MUTEX_NAME)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    already_exists = ctypes.get_last_error() == WINDOWS_ERROR_ALREADY_EXISTS
    return int(handle), already_exists


def _release_single_instance_mutex(handle: int | None) -> None:
    if handle is None or os.name != "nt":
        return
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_bool
    close_handle(ctypes.c_void_p(handle))


def port_is_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
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
            payload = json.load(response)
            return int(response.status) == 200 and payload == {
                "status": "ok",
                "engine": "monte-carlo-simulator",
            }
    except (OSError, URLError, json.JSONDecodeError):
        return False


def find_running_server(host: str, preferred: int = DEFAULT_PORT) -> str | None:
    """Return the URL of an existing RiskSim instance in the port range."""
    for candidate in range(preferred, preferred + PORT_SEARCH_ATTEMPTS):
        url = f"http://{host}:{candidate}"
        if server_is_ready(url):
            return url
    return None


def wait_for_running_server(
    host: str,
    preferred: int = DEFAULT_PORT,
    *,
    timeout: float = EXISTING_INSTANCE_TIMEOUT_SECONDS,
) -> str | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if url := find_running_server(host, preferred):
            return url
        time.sleep(SERVER_READY_POLL_INTERVAL_SECONDS)
    return None


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


def _configure_logging() -> None:
    """Send launcher and server diagnostics to the visible terminal."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _listen_for_shutdown_commands(
    server: ShutdownServer, stream: TextIO | None = None
) -> None:
    """Translate simple terminal commands into a graceful Uvicorn shutdown."""
    source = stream if stream is not None else sys.stdin
    while not bool(getattr(server, "should_exit", False)):
        try:
            line = source.readline()
        except (OSError, UnicodeError):
            return
        if line == "":
            return
        command = line.strip().casefold()
        if not command:
            continue
        if command in STOP_COMMANDS:
            print("\nArrêt demandé depuis le terminal. Fermeture de RiskSim...")
            server.should_exit = True
            return
        print("Commande inconnue. Utilisez exit, quit, q ou Ctrl+C pour arrêter RiskSim.")


def _start_shutdown_command_listener(server: ShutdownServer) -> threading.Thread:
    thread = threading.Thread(
        target=_listen_for_shutdown_commands,
        args=(server,),
        name="risksim-terminal-commands",
        daemon=True,
    )
    thread.start()
    return thread


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
    # Imported here so a missing or damaged bundled dependency is caught by
    # the diagnostic launcher instead of closing its console immediately.
    import uvicorn

    _configure_logging()
    options = build_parser().parse_args(argv)

    mutex_handle, already_running = _acquire_single_instance_mutex()
    if already_running:
        _release_single_instance_mutex(mutex_handle)
        url = wait_for_running_server(HOST, options.port)
        if url is None:
            raise RuntimeError(
                "Une instance de RiskSim démarre déjà, mais elle n'a pas encore répondu."
            )
        print(f"RiskSim est déjà actif sur {url}.")
        print("Le navigateur va afficher l'instance existante.")
        if not options.no_browser:
            webbrowser.open(url)
        return

    try:
        port = choose_port(HOST, options.port)

        if frontend_directory() is None:
            logger.warning(
                "L'interface construite est introuvable : seule l'API répondra. "
                "Depuis les sources, lancez « npm run build » dans web/ au préalable."
            )

        url = f"http://{HOST}:{port}"
        print("=" * 62)
        print("RiskSim — Monte Carlo")
        print("=" * 62)
        print(f"Interface locale : {url}")
        print("Le navigateur s'ouvrira dès que le moteur sera prêt.")
        print("Pour arrêter proprement : Ctrl+C, exit, quit ou q.")
        print("Les données restent sur cette machine.\n")
        if not options.no_browser:
            _open_browser_when_ready(url)

        from monte_carlo_simulator.web_api import app

        config = uvicorn.Config(
            app,
            host=HOST,
            port=port,
            reload=False,
            log_level="info",
            log_config=uvicorn.config.LOGGING_CONFIG,
            access_log=True,
            use_colors=True,
        )
        server = uvicorn.Server(config)
        app.state.shutdown_callback = lambda: setattr(server, "should_exit", True)
        _start_shutdown_command_listener(server)
        try:
            server.run()
            print("\nRiskSim est arrêté. Vous pouvez fermer cette fenêtre et déplacer le dossier.")
        finally:
            if hasattr(app.state, "shutdown_callback"):
                del app.state.shutdown_callback
    finally:
        _release_single_instance_mutex(mutex_handle)


if __name__ == "__main__":  # pragma: no cover - entry point
    try:
        main()
    except KeyboardInterrupt:
        print("\nArrêt demandé. RiskSim est fermé.")
    except BaseException:
        _report_startup_failure()
        raise SystemExit(1) from None
