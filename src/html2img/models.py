"""Request and response objects for the html2img API.

The two request dataclasses map directly onto the JSON bodies of
``POST /api/html`` and ``POST /api/screenshot``. Any option left as ``None`` is
omitted from the request, so the server applies its own default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Union

from html2img import _guard
from html2img.enums import Format

__all__ = ["HtmlRequest", "RenderResponse", "ScreenshotRequest"]

FormatLike = Union[Format, str, None]


@dataclass
class HtmlRequest:
    """A request to render an HTML document to an image or PDF.

    Only :attr:`html` is required.

    :param html: A complete HTML document to render. Inline your CSS in a
        ``<style>`` block, or reference remote stylesheets and web fonts with
        ``<link>`` tags in the document head.
    :param css: Extra CSS injected after the document loads, on top of any
        styles in the HTML.
    :param width: Viewport width in CSS pixels (1 to 5000).
    :param height: Viewport height in CSS pixels (1 to 5000). Ignored when
        ``fullpage`` is true.
    :param fullpage: Grow the image to the full rendered height of the document.
    :param dpi: Device pixel ratio multiplier (1 to 4). 1 is standard, 2 is retina.
    :param webhook_url: Switch to async mode and POST the final image URL here
        once rendering finishes.
    :param ms_delay: Wait this many milliseconds after load before capturing
        (1 to 5000).
    :param wait_for_selector: Wait until this CSS selector appears in the DOM
        before capturing.
    :param format: Output format. Defaults to PNG server-side.
    :param scale_to_fit: PDF only. Scale wide content down to the page width
        instead of clipping it.
    """

    html: str
    css: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fullpage: Optional[bool] = None
    dpi: Optional[int] = None
    webhook_url: Optional[str] = None
    ms_delay: Optional[int] = None
    wait_for_selector: Optional[str] = None
    format: FormatLike = None
    scale_to_fit: Optional[bool] = None

    def __post_init__(self) -> None:
        self.html = _guard.required_string("html", self.html)
        self.css = _guard.optional_string("css", self.css)
        self.width = _guard.dimension("width", self.width)
        self.height = _guard.dimension("height", self.height)
        self.fullpage = _guard.optional_bool("fullpage", self.fullpage)
        self.dpi = _guard.dpi(self.dpi)
        self.webhook_url = _guard.optional_string("webhook_url", self.webhook_url)
        self.ms_delay = _guard.ms_delay(self.ms_delay)
        self.wait_for_selector = _guard.optional_string("wait_for_selector", self.wait_for_selector)
        self.format = Format.coerce(self.format)
        self.scale_to_fit = _guard.optional_bool("scale_to_fit", self.scale_to_fit)

    def to_dict(self) -> Dict[str, Any]:
        """Build the JSON request body, omitting any option left as ``None``."""
        return _compact(
            {
                "html": self.html,
                "css": self.css,
                "width": self.width,
                "height": self.height,
                "fullpage": self.fullpage,
                "dpi": self.dpi,
                "webhook_url": self.webhook_url,
                "ms_delay": self.ms_delay,
                "wait_for_selector": self.wait_for_selector,
                "format": self.format.value if isinstance(self.format, Format) else None,
                "scale_to_fit": self.scale_to_fit,
            }
        )


@dataclass
class ScreenshotRequest:
    """A request to capture a screenshot of a live, publicly reachable URL.

    Only :attr:`url` is required.

    :param url: The fully qualified, publicly reachable URL to capture.
    :param css: Extra CSS injected after the page loads, for example to hide
        cookie banners or chat widgets.
    :param width: Viewport width in CSS pixels (1 to 5000).
    :param height: Viewport height in CSS pixels (1 to 5000). Ignored when
        ``fullpage`` is true.
    :param fullpage: Capture the full scroll length of the page instead of only
        the viewport.
    :param selector: CSS selector used to crop the capture to a single element.
    :param dpi: Device pixel ratio multiplier (1 to 4). 1 is standard, 2 is retina.
    :param webhook_url: Switch to async mode and POST the final image URL here
        once rendering finishes.
    :param ms_delay: Wait this many milliseconds after load before capturing
        (1 to 5000).
    :param wait_for_selector: Wait until this CSS selector appears in the DOM
        before capturing.
    :param format: Output format. Defaults to PNG server-side.
    :param scale_to_fit: PDF only. Scale wide content down to the page width
        instead of clipping it.
    """

    url: str
    css: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fullpage: Optional[bool] = None
    selector: Optional[str] = None
    dpi: Optional[int] = None
    webhook_url: Optional[str] = None
    ms_delay: Optional[int] = None
    wait_for_selector: Optional[str] = None
    format: FormatLike = None
    scale_to_fit: Optional[bool] = None

    def __post_init__(self) -> None:
        self.url = _guard.required_string("url", self.url)
        self.css = _guard.optional_string("css", self.css)
        self.width = _guard.dimension("width", self.width)
        self.height = _guard.dimension("height", self.height)
        self.fullpage = _guard.optional_bool("fullpage", self.fullpage)
        self.selector = _guard.optional_string("selector", self.selector)
        self.dpi = _guard.dpi(self.dpi)
        self.webhook_url = _guard.optional_string("webhook_url", self.webhook_url)
        self.ms_delay = _guard.ms_delay(self.ms_delay)
        self.wait_for_selector = _guard.optional_string("wait_for_selector", self.wait_for_selector)
        self.format = Format.coerce(self.format)
        self.scale_to_fit = _guard.optional_bool("scale_to_fit", self.scale_to_fit)

    def to_dict(self) -> Dict[str, Any]:
        """Build the JSON request body, omitting any option left as ``None``."""
        return _compact(
            {
                "url": self.url,
                "css": self.css,
                "width": self.width,
                "height": self.height,
                "fullpage": self.fullpage,
                "selector": self.selector,
                "dpi": self.dpi,
                "webhook_url": self.webhook_url,
                "ms_delay": self.ms_delay,
                "wait_for_selector": self.wait_for_selector,
                "format": self.format.value if isinstance(self.format, Format) else None,
                "scale_to_fit": self.scale_to_fit,
            }
        )


@dataclass(frozen=True)
class RenderResponse:
    """The result of a successful render call.

    Covers both the synchronous envelope (:attr:`url` populated) and the
    asynchronous acceptance envelope returned when a ``webhook_url`` was
    supplied (:attr:`status` is ``"processing"`` and :attr:`url` is ``None``
    until the webhook fires).
    """

    success: bool = False
    id: Optional[str] = None
    url: Optional[str] = None
    expires_at: Optional[str] = None
    """When a hosted render expires, as an ISO 8601 string.

    ``None`` on paid plans, where renders stay hosted permanently; set on
    free-tier renders, which are hosted for seven days.
    """
    credits_remaining: Optional[int] = None
    status: Optional[str] = None
    message: Optional[str] = None
    template: Optional[str] = None
    raw: Mapping[str, Any] = field(default_factory=dict)
    """The full decoded JSON payload, for any field not surfaced as an attribute."""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RenderResponse:
        """Build a response from a decoded JSON payload."""
        return cls(
            success=bool(data.get("success", False)),
            id=_as_str(data.get("id")),
            url=_as_str(data.get("url")),
            expires_at=_as_str(data.get("expires_at")),
            credits_remaining=_as_int(data.get("credits_remaining")),
            status=_as_str(data.get("status")),
            message=_as_str(data.get("message")),
            template=_as_str(data.get("template")),
            raw=dict(data),
        )

    @property
    def is_processing(self) -> bool:
        """Whether this is an async job still being rendered.

        When true, the final image URL is delivered to the request's
        ``webhook_url`` rather than being available on this response.
        """
        return self.status == "processing"

    @property
    def is_pdf(self) -> bool:
        """Whether the render came back as a PDF rather than an image."""
        return bool(self.url) and str(self.url).lower().split("?")[0].endswith(".pdf")

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.url or ""


def _compact(body: Mapping[str, Any]) -> Dict[str, Any]:
    """Drop every ``None`` value so the server applies its own defaults."""
    return {key: value for key, value in body.items() if value is not None}


def _as_str(value: Any) -> Optional[str]:
    if value is None or isinstance(value, (dict, list)):
        return None

    return str(value)


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None

    if isinstance(value, int):
        return value

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
