"""The synchronous html2img API client."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Union
from urllib.parse import quote

from html2img import _guard
from html2img.exceptions import (
    AuthenticationError,
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
from html2img.transport import USER_AGENT, Transport, UrllibTransport

__all__ = ["Html2img"]

ImageLike = Union[RenderResponse, str]

HTML_PATH = "/api/html"
SCREENSHOT_PATH = "/api/screenshot"
TEMPLATE_PATH = "/api/v1/templates"


class Html2img:
    """Client for the html2img.com API.

    Render HTML documents you control, capture live URLs, or render named
    templates, each returning a :class:`~html2img.models.RenderResponse`. Every
    failure surfaces as an :class:`~html2img.exceptions.Html2imgError`; no raw
    ``urllib`` error escapes.

    .. code-block:: python

        from html2img import Html2img

        client = Html2img()  # reads HTML2IMG_API_KEY from the environment
        response = client.html("<h1>Hello</h1>", width=1200, height=630)
        print(response.url)

    :param api_key: Your API key, sent as the ``X-API-Key`` header. Falls back
        to the ``HTML2IMG_API_KEY`` environment variable.
    :param base_url: Base URL of the API. Falls back to ``HTML2IMG_BASE_URI``,
        then to :attr:`DEFAULT_BASE_URL`. Override only for testing or a private
        deployment.
    :param timeout: Request timeout in seconds. Defaults to just over the 30
        second synchronous render budget.
    :param transport: An optional callable used to perform HTTP requests. See
        :mod:`html2img.transport`. When supplied it is used as is; the client
        still sends the ``X-API-Key``, ``Accept`` and ``Content-Type`` headers
        on every request.
    """

    DEFAULT_BASE_URL = "https://app.html2img.com"
    DEFAULT_TIMEOUT = 35.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[Transport] = None,
    ) -> None:
        resolved_key = api_key if api_key is not None else os.environ.get("HTML2IMG_API_KEY")

        if not resolved_key:
            raise ValueError(
                "No html2img API key. Pass api_key=... or set the HTML2IMG_API_KEY "
                "environment variable. Create a free key at "
                "https://app.html2img.com/register."
            )

        resolved_base = (
            base_url
            if base_url is not None
            else os.environ.get("HTML2IMG_BASE_URI") or self.DEFAULT_BASE_URL
        )

        self._api_key = _guard.required_string("api_key", resolved_key)
        self.base_url = _guard.required_string("base_url", resolved_base).rstrip("/")
        self.timeout = _guard.timeout(timeout if timeout is not None else self.DEFAULT_TIMEOUT)
        self._transport: Transport = transport or UrllibTransport()

    # ------------------------------------------------------------------
    # Render endpoints
    # ------------------------------------------------------------------

    def html(self, html: Union[str, HtmlRequest], **options: Any) -> RenderResponse:
        """Render an HTML document to an image or PDF (``POST /api/html``).

        Pass the document and any options as keyword arguments, or build a
        :class:`~html2img.models.HtmlRequest` yourself.

        .. code-block:: python

            client.html("<h1>Hello</h1>", width=1200, height=630, dpi=2)
            client.html(HtmlRequest(html=document, format="pdf"))

        :raises html2img.Html2imgError: on any API or transport failure.
        """
        request = html if isinstance(html, HtmlRequest) else HtmlRequest(html=html, **options)

        return self._send(HTML_PATH, request.to_dict())

    def screenshot(self, url: Union[str, ScreenshotRequest], **options: Any) -> RenderResponse:
        """Capture a screenshot of a live URL (``POST /api/screenshot``).

        .. code-block:: python

            client.screenshot("https://example.com", width=1200, fullpage=True)

        :raises html2img.Html2imgError: on any API or transport failure.
        """
        request = (
            url if isinstance(url, ScreenshotRequest) else ScreenshotRequest(url=url, **options)
        )

        return self._send(SCREENSHOT_PATH, request.to_dict())

    def template(
        self,
        slug: str,
        data: Optional[Mapping[str, Any]] = None,
        **fields: Any,
    ) -> RenderResponse:
        """Render a named template from a data payload.

        ``POST /api/v1/templates/{slug}``. The data is validated server-side per
        template. Templates output PNG only.

        .. code-block:: python

            client.template("invoice-image", {"number": 1042, "amount": "£240.00"})
            client.template("invoice-image", number=1042, amount="£240.00")

        :param slug: The template slug, for example ``invoice-image``.
        :param data: The template data, as a mapping.
        :param fields: Template data as keyword arguments, merged over ``data``.
        :raises html2img.Html2imgError: on any API or transport failure.
        """
        _guard.required_string("slug", slug)

        payload: Dict[str, Any] = dict(data or {})
        payload.update(fields)

        return self._send(f"{TEMPLATE_PATH}/{quote(slug, safe='')}", payload)

    # ------------------------------------------------------------------
    # Working with the result
    # ------------------------------------------------------------------

    def download(self, image: ImageLike) -> bytes:
        """Download the rendered bytes from a render's CDN URL.

        Accepts a :class:`~html2img.models.RenderResponse` or a URL string.

        :raises html2img.Html2imgError: if the render has no URL yet, or the
            download fails.
        """
        url = self._url_for(image)

        status, body = self._transport(
            method="GET",
            url=url,
            headers={"Accept": "*/*", "User-Agent": USER_AGENT},
            body=None,
            timeout=self.timeout,
        )

        if status >= 400:
            raise Html2imgError(
                f"Could not download the render from {url}: HTTP {status}.",
                status_code=status,
            )

        return body

    def save(self, image: ImageLike, path: Union[str, os.PathLike[str]]) -> Path:
        """Download a render and write it to a local file.

        Parent directories are created for you. Returns the path written.

        .. code-block:: python

            response = client.html(document, width=1200, height=630)
            client.save(response, "og/post-42.png")

        :raises html2img.Html2imgError: if the render has no URL yet, or the
            download fails.
        """
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.download(image))

        return target

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _send(self, path: str, body: Mapping[str, Any]) -> RenderResponse:
        status, raw = self._transport(
            method="POST",
            url=f"{self.base_url}{path}",
            headers=self._headers(),
            body=json.dumps(body).encode("utf-8"),
            timeout=self.timeout,
        )

        payload = _decode(raw)

        if status >= 400:
            raise _error_for(status, payload)

        return RenderResponse.from_dict(payload)

    def _headers(self) -> Dict[str, str]:
        """The headers sent on every API request."""
        return {
            "X-API-Key": self._api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
        }

    @staticmethod
    def _url_for(image: ImageLike) -> str:
        if isinstance(image, RenderResponse):
            if not image.url:
                raise Html2imgError(
                    "The render has no image URL yet. Async jobs deliver their URL "
                    "to the configured webhook."
                )

            return image.url

        return _guard.required_string("image url", image)

    def __enter__(self) -> Html2img:
        return self

    def __exit__(self, *exc_info: Any) -> None:
        return None

    def __repr__(self) -> str:
        return f"Html2img(base_url={self.base_url!r}, timeout={self.timeout!r})"


def _decode(body: bytes) -> Dict[str, Any]:
    """Decode a JSON body, tolerating an empty or malformed response."""
    if not body:
        return {}

    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}

    return decoded if isinstance(decoded, dict) else {}


def _error_for(status: int, payload: Mapping[str, Any]) -> Html2imgError:
    """Map an error response onto the matching exception type."""
    error_code = payload.get("code") if isinstance(payload.get("code"), str) else None
    message = _message_from(payload, status)

    if status in (400, 422):
        return ValidationError(
            message,
            details=_details_from(payload),
            status_code=status,
            payload=payload,
            error_code=error_code,
        )

    kinds = {
        401: AuthenticationError,
        402: InsufficientCreditsError,
        403: NotSubscribedError,
        404: NotFoundError,
        408: TimeoutError,
        429: RateLimitError,
        504: TimeoutError,
    }

    kind = kinds.get(status)

    if kind is None:
        kind = ServerError if status >= 500 else Html2imgError

    return kind(message, status_code=status, payload=payload, error_code=error_code)


def _message_from(payload: Mapping[str, Any], status: int) -> str:
    """Derive a human-readable message from the response body."""
    for key in ("error", "message"):
        value = payload.get(key)

        if isinstance(value, str) and value:
            return value

    return f"The html2img API returned HTTP {status}."


def _details_from(payload: Mapping[str, Any]) -> Dict[str, List[str]]:
    """Extract the per-field validation messages from a validation response."""
    details = payload.get("details")

    if not isinstance(details, Mapping):
        return {}

    result: Dict[str, List[str]] = {}

    for field_name, messages in details.items():
        if isinstance(messages, (list, tuple)):
            result[str(field_name)] = [str(message) for message in messages]
        else:
            result[str(field_name)] = [str(messages)]

    return result
