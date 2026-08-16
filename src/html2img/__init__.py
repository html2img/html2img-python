"""Official Python client for the html2img.com HTML to Image API.

Turn HTML and CSS into images, capture screenshots of live URLs, render named
templates, and export A4 PDFs. Every render runs in real Chrome, so flexbox,
grid, custom properties, web fonts and inline JavaScript behave exactly as they
do in the browser.

.. code-block:: python

    from html2img import Html2img

    client = Html2img()  # reads HTML2IMG_API_KEY from the environment

    response = client.html("<h1>Hello</h1>", width=1200, height=630, dpi=2)
    print(response.url)

Documentation: https://html2img.com/docs
"""

from __future__ import annotations

from html2img._version import __version__
from html2img.aio import AsyncHtml2img
from html2img.client import Html2img
from html2img.enums import Format
from html2img.exceptions import (
    AuthenticationError,
    ConnectionError,
    Html2imgError,
    InsufficientCreditsError,
    NotFoundError,
    NotSubscribedError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from html2img.models import HtmlRequest, RenderResponse, ScreenshotRequest
from html2img.transport import Transport, UrllibTransport

__all__ = [
    "AsyncHtml2img",
    "AuthenticationError",
    "ConnectionError",
    "Format",
    "Html2img",
    "Html2imgError",
    "HtmlRequest",
    "InsufficientCreditsError",
    "NotFoundError",
    "NotSubscribedError",
    "RateLimitError",
    "RenderResponse",
    "ScreenshotRequest",
    "ServerError",
    "TimeoutError",
    "Transport",
    "UrllibTransport",
    "ValidationError",
    "__version__",
]
