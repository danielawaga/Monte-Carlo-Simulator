"""Tests for resource resolution and the desktop launcher."""

from __future__ import annotations

import socket
import sys
from pathlib import Path

import pytest

from monte_carlo_simulator import launcher, resources


class TestResourceResolution:
    def test_the_source_tree_resolves_relative_to_the_repository(self) -> None:
        assert resources.is_frozen() is False
        assert (resources.resource_path("data", "templates")).is_dir()

    def test_a_frozen_build_resolves_relative_to_its_unpack_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Paths computed from __file__ point nowhere inside a packaged build."""
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

        assert resources.is_frozen() is True
        assert resources.resource_root() == tmp_path
        assert resources.resource_path("data", "x.xlsx") == tmp_path / "data" / "x.xlsx"

    def test_the_frontend_is_reported_only_once_it_is_built(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

        assert resources.frontend_directory() is None, "un dossier absent ne doit pas être servi"

        dist = tmp_path / "web" / "dist"
        dist.mkdir(parents=True)
        (dist / "index.html").write_text("<!doctype html>", encoding="utf-8")

        assert resources.frontend_directory() == dist


class TestPortSelection:
    def test_a_free_port_is_taken_as_is(self) -> None:
        assert launcher.choose_port("127.0.0.1", _an_unused_port()) is not None

    def test_an_occupied_port_makes_the_launcher_move_on(self) -> None:
        """A second launch must not end in a stack trace nobody is watching."""
        busy = _an_unused_port()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as held:
            held.bind(("127.0.0.1", busy))
            held.listen(1)

            chosen = launcher.choose_port("127.0.0.1", busy)

            assert chosen != busy
            assert chosen > busy

    def test_giving_up_is_explicit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(launcher, "port_is_free", lambda *_: False)

        with pytest.raises(SystemExit, match="Aucun port libre"):
            launcher.choose_port("127.0.0.1", 8000)


class TestBrowserOpening:
    def test_the_browser_opens_only_after_the_health_endpoint_answers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        answers = iter([False, False, True])
        probes: list[str] = []
        sleeps: list[float] = []
        opened: list[str] = []

        def probe(url: str) -> bool:
            probes.append(url)
            return next(answers)

        monkeypatch.setattr(launcher, "server_is_ready", probe)
        monkeypatch.setattr(launcher.time, "sleep", sleeps.append)
        monkeypatch.setattr(launcher.webbrowser, "open", opened.append)

        launcher._wait_for_server_and_open_browser(
            "http://127.0.0.1:8000", timeout=1.0, poll_interval=0.05
        )

        assert probes == ["http://127.0.0.1:8000"] * 3
        assert sleeps == [0.05, 0.05]
        assert opened == ["http://127.0.0.1:8000"]

    def test_a_failed_probe_does_not_open_an_error_page(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        clock = iter([0.0, 0.5, 1.1])
        opened: list[str] = []

        monkeypatch.setattr(launcher, "server_is_ready", lambda _url: False)
        monkeypatch.setattr(launcher.time, "monotonic", lambda: next(clock))
        monkeypatch.setattr(launcher.time, "sleep", lambda _delay: None)
        monkeypatch.setattr(launcher.webbrowser, "open", opened.append)

        launcher._wait_for_server_and_open_browser("http://127.0.0.1:8000", timeout=1.0)

        assert opened == []


class TestCommandLine:
    def test_the_listening_address_cannot_be_changed(self) -> None:
        """The application has no authentication, so a non-loopback bind would
        let any device on the subnet read and delete the saved registers."""
        assert launcher.HOST == "127.0.0.1"

        with pytest.raises(SystemExit):
            launcher.build_parser().parse_args(["--host", "0.0.0.0"])

    def test_the_defaults_are_usable_as_is(self) -> None:
        options = launcher.build_parser().parse_args([])

        assert options.port == launcher.DEFAULT_PORT
        assert options.no_browser is False

    def test_the_environment_can_preset_the_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MCS_PORT", "9100")

        assert launcher.build_parser().parse_args([]).port == 9100

    def test_explicit_arguments_win_over_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("MCS_PORT", "9100")

        options = launcher.build_parser().parse_args(["--port", "9200", "--no-browser"])

        assert options.port == 9200
        assert options.no_browser is True


def _an_unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])
