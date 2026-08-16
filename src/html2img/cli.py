"""Command line interface for the html2img client.

Installed as the ``html2img`` command:

.. code-block:: console

    $ html2img test
    $ html2img html card.html --width 1200 --height 630 --out card.png
    $ html2img screenshot https://example.com --fullpage --out shot.png
    $ html2img template invoice-image --data '{"number": 1042}'
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Optional, Sequence

from html2img._version import __version__
from html2img.client import Html2img
from html2img.exceptions import Html2imgError, ValidationError
from html2img.models import RenderResponse

TEST_DOCUMENT = (
    '<!doctype html><html><body style="font-family:system-ui;display:flex;'
    "align-items:center;justify-content:center;height:180px;margin:0;"
    'background:#0f172a;color:#fff"><h1>html2img is configured</h1></body></html>'
)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point for the ``html2img`` command. Returns a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    try:
        client = Html2img(api_key=args.api_key, base_url=args.base_url, timeout=args.timeout)
    except ValueError as error:
        return _fail(str(error))

    try:
        response = _run(client, args)
    except ValidationError as error:
        _fail(str(error))

        for field, messages in error.details.items():
            for message in messages:
                print(f"  {field}: {message}", file=sys.stderr)

        return 1
    except Html2imgError as error:
        return _fail(f"Request failed: {error}")
    except (ValueError, TypeError, OSError) as error:
        return _fail(str(error))

    return _report(client, response, args)


def _run(client: Html2img, args: argparse.Namespace) -> RenderResponse:
    if args.command == "test":
        return client.html(TEST_DOCUMENT, width=600, height=200)

    if args.command == "html":
        return client.html(_read_document(args.source), **_render_options(args))

    if args.command == "screenshot":
        options = _render_options(args)

        if args.selector:
            options["selector"] = args.selector

        return client.screenshot(args.url, **options)

    if args.command == "template":
        return client.template(args.slug, _template_data(args.data))

    raise ValueError(f"Unknown command: {args.command}")  # pragma: no cover - argparse guards


def _report(client: Html2img, response: RenderResponse, args: argparse.Namespace) -> int:
    if args.command == "test":
        print("Test render succeeded.")

    if response.is_processing:
        print("Accepted. The final URL will be delivered to your webhook.")
        return 0

    if not response.url:
        return _fail("The API returned no image URL.")

    print(response.url)

    out = getattr(args, "out", None)

    if out:
        path = client.save(response, out)
        print(f"Saved to {path}")

    if response.credits_remaining is not None:
        print(f"Credits remaining: {response.credits_remaining}")

    return 0


def _render_options(args: argparse.Namespace) -> Dict[str, Any]:
    options: Dict[str, Any] = {}

    for name in ("width", "height", "dpi", "ms_delay", "css", "wait_for_selector", "webhook_url"):
        value = getattr(args, name, None)

        if value is not None:
            options[name] = value

    if getattr(args, "fullpage", False):
        options["fullpage"] = True

    if getattr(args, "format", None):
        options["format"] = args.format

    return options


def _read_document(source: str) -> str:
    """Read an HTML document from a file path, or from stdin when given ``-``."""
    if source == "-":
        return sys.stdin.read()

    with open(source, encoding="utf-8") as handle:
        return handle.read()


def _template_data(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}

    if raw == "-":
        raw = sys.stdin.read()
    elif raw.startswith("@"):
        with open(raw[1:], encoding="utf-8") as handle:
            raw = handle.read()

    decoded = json.loads(raw)

    if not isinstance(decoded, dict):
        raise ValueError("Template data must be a JSON object.")

    return decoded


def _fail(message: str) -> int:
    print(message, file=sys.stderr)

    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="html2img",
        description="Render HTML, capture screenshots and export PDFs with html2img.com.",
        epilog="Documentation: https://html2img.com/docs",
    )
    parser.add_argument("--version", action="version", version=f"html2img {__version__}")
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key. Defaults to the HTML2IMG_API_KEY environment variable.",
    )
    parser.add_argument("--base-url", default=None, help=argparse.SUPPRESS)
    parser.add_argument(
        "--timeout", type=float, default=None, help="Request timeout in seconds (default 35)."
    )

    commands = parser.add_subparsers(dest="command")

    commands.add_parser(
        "test",
        help="Render a small test image to verify your configuration (uses one credit).",
    )

    html = commands.add_parser("html", help="Render an HTML file (or stdin) to an image or PDF.")
    html.add_argument("source", help="Path to an HTML file, or - to read stdin.")
    _add_render_options(html)

    screenshot = commands.add_parser("screenshot", help="Capture a screenshot of a live URL.")
    screenshot.add_argument("url", help="The publicly reachable URL to capture.")
    screenshot.add_argument("--selector", help="Crop the capture to this CSS selector.")
    _add_render_options(screenshot)

    template = commands.add_parser("template", help="Render a named template.")
    template.add_argument("slug", help="The template slug, for example invoice-image.")
    template.add_argument(
        "--data",
        help="Template data as JSON, @path/to/file.json, or - to read stdin.",
    )
    template.add_argument("--out", "-o", help="Also save the render to this path.")

    return parser


def _add_render_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--width", type=int, help="Viewport width in CSS pixels (1 to 5000).")
    parser.add_argument("--height", type=int, help="Viewport height in CSS pixels (1 to 5000).")
    parser.add_argument("--dpi", type=int, help="Device pixel ratio (1 to 4). Use 2 for retina.")
    parser.add_argument("--fullpage", action="store_true", help="Capture the full page height.")
    parser.add_argument("--css", help="Extra CSS injected after load.")
    parser.add_argument("--format", choices=["png", "pdf"], help="Output format (default png).")
    parser.add_argument("--ms-delay", type=int, dest="ms_delay", help="Delay before capture (ms).")
    parser.add_argument(
        "--wait-for-selector",
        dest="wait_for_selector",
        help="Wait for this CSS selector before capturing.",
    )
    parser.add_argument(
        "--webhook-url", dest="webhook_url", help="Deliver the result to this webhook instead."
    )
    parser.add_argument("--out", "-o", help="Also save the render to this path.")


def _entrypoint() -> None:  # pragma: no cover - console script shim
    sys.exit(main())


if __name__ == "__main__":  # pragma: no cover
    _entrypoint()
