"""The `html2img` command line interface."""

from __future__ import annotations

import json
from typing import Any

import pytest

from html2img import cli
from tests.conftest import FakeTransport

RENDERED = {
    "success": True,
    "id": "abc123",
    "url": "https://i.html2img.com/abc123.png",
    "credits_remaining": 49,
}


@pytest.fixture
def stub(monkeypatch: pytest.MonkeyPatch) -> FakeTransport:
    """Point every client the CLI builds at a fake transport."""
    transport = FakeTransport((200, RENDERED))
    original = cli.Html2img

    def build(**kwargs: Any) -> Any:
        return original(**{**kwargs, "transport": transport})

    monkeypatch.setattr(cli, "Html2img", build)
    monkeypatch.setenv("HTML2IMG_API_KEY", "test-key")

    return transport


def test_it_prints_help_with_no_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main([]) == 0
    assert "usage: html2img" in capsys.readouterr().out


def test_test_command_renders_and_reports(
    stub: FakeTransport, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["test"]) == 0

    out = capsys.readouterr().out

    assert "Test render succeeded." in out
    assert "https://i.html2img.com/abc123.png" in out
    assert "Credits remaining: 49" in out
    assert stub.last["body"]["width"] == 600


def test_it_fails_clearly_without_an_api_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("HTML2IMG_API_KEY", raising=False)

    assert cli.main(["test"]) == 1
    assert "HTML2IMG_API_KEY" in capsys.readouterr().err


def test_html_command_reads_a_file_and_passes_options(stub: FakeTransport, tmp_path) -> None:
    source = tmp_path / "card.html"
    source.write_text("<h1>Hi</h1>", encoding="utf-8")

    assert cli.main(["html", str(source), "--width", "1200", "--dpi", "2", "--format", "pdf"]) == 0
    assert stub.last["body"] == {"html": "<h1>Hi</h1>", "width": 1200, "dpi": 2, "format": "pdf"}


def test_html_command_reads_stdin(stub: FakeTransport, monkeypatch: pytest.MonkeyPatch) -> None:
    import io

    monkeypatch.setattr("sys.stdin", io.StringIO("<h1>From stdin</h1>"))

    assert cli.main(["html", "-"]) == 0
    assert stub.last["body"]["html"] == "<h1>From stdin</h1>"


def test_screenshot_command_passes_the_selector_and_fullpage(stub: FakeTransport) -> None:
    assert cli.main(["screenshot", "https://example.com", "--selector", "#hero", "--fullpage"]) == 0
    assert stub.last["body"] == {
        "url": "https://example.com",
        "selector": "#hero",
        "fullpage": True,
    }


def test_template_command_sends_json_data(stub: FakeTransport) -> None:
    assert cli.main(["template", "invoice-image", "--data", json.dumps({"number": 7})]) == 0
    assert stub.last["url"].endswith("/api/v1/templates/invoice-image")
    assert stub.last["body"] == {"number": 7}


def test_it_saves_the_render_when_asked(
    stub: FakeTransport, tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "card.html"
    source.write_text("<h1>Hi</h1>", encoding="utf-8")
    target = tmp_path / "out" / "card.png"

    stub.queued = [(200, RENDERED), (200, b"png-bytes")]

    assert cli.main(["html", str(source), "--out", str(target)]) == 0
    assert target.read_bytes() == b"png-bytes"
    assert f"Saved to {target}" in capsys.readouterr().out


def test_it_reports_validation_details(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    transport = FakeTransport(
        (422, {"error": "Invalid.", "details": {"width": ["Must be 1 to 5000."]}})
    )
    original = cli.Html2img
    monkeypatch.setattr(cli, "Html2img", lambda **kw: original(**{**kw, "transport": transport}))
    monkeypatch.setenv("HTML2IMG_API_KEY", "test-key")

    assert cli.main(["test"]) == 1

    err = capsys.readouterr().err

    assert "Invalid." in err
    assert "width: Must be 1 to 5000." in err


def test_it_reports_an_async_acceptance(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    transport = FakeTransport((200, {"success": True, "status": "processing"}))
    original = cli.Html2img
    monkeypatch.setattr(cli, "Html2img", lambda **kw: original(**{**kw, "transport": transport}))
    monkeypatch.setenv("HTML2IMG_API_KEY", "test-key")

    assert cli.main(["screenshot", "https://example.com", "--webhook-url", "https://x.test/h"]) == 0
    assert "delivered to your webhook" in capsys.readouterr().out
