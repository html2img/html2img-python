"""The asyncio client.

:class:`AsyncHtml2img` mirrors :class:`~html2img.client.Html2img` method for
method, awaiting each call instead of blocking. Requests run on the default
thread pool executor via :func:`asyncio.to_thread`, which keeps the package
free of runtime dependencies while leaving the event loop free during a render.

A render is a single request that takes anywhere from a few hundred
milliseconds to the full 30 second budget, so the thread pool is rarely the
bottleneck. If you want renders to share your application's own connection
pool, pass an ``httpx``- or ``aiohttp``-backed callable as ``transport``
instead (see :mod:`html2img.transport`).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from html2img.client import Html2img, ImageLike
from html2img.models import HtmlRequest, RenderResponse, ScreenshotRequest
from html2img.transport import Transport

__all__ = ["AsyncHtml2img"]


class AsyncHtml2img:
    """Asyncio client for the html2img.com API.

    .. code-block:: python

        import asyncio
        from html2img import AsyncHtml2img

        async def main():
            async with AsyncHtml2img() as client:
                response = await client.html("<h1>Hello</h1>", width=1200, height=630)
                print(response.url)

        asyncio.run(main())

    Takes the same arguments as :class:`~html2img.client.Html2img`.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        transport: Optional[Transport] = None,
    ) -> None:
        self._client = Html2img(
            api_key,
            base_url=base_url,
            timeout=timeout,
            transport=transport,
        )

    @property
    def base_url(self) -> str:
        """The API base URL in use."""
        return self._client.base_url

    @property
    def timeout(self) -> float:
        """The per-request timeout in seconds."""
        return self._client.timeout

    @property
    def sync(self) -> Html2img:
        """The underlying synchronous client."""
        return self._client

    async def html(self, html: Union[str, HtmlRequest], **options: Any) -> RenderResponse:
        """Render an HTML document to an image or PDF."""
        return await asyncio.to_thread(self._client.html, html, **options)

    async def screenshot(
        self, url: Union[str, ScreenshotRequest], **options: Any
    ) -> RenderResponse:
        """Capture a screenshot of a live URL."""
        return await asyncio.to_thread(self._client.screenshot, url, **options)

    async def template(
        self,
        slug: str,
        data: Optional[Mapping[str, Any]] = None,
        **fields: Any,
    ) -> RenderResponse:
        """Render a named template from a data payload."""
        return await asyncio.to_thread(self._client.template, slug, data, **fields)

    async def download(self, image: ImageLike) -> bytes:
        """Download the rendered bytes from a render's CDN URL."""
        return await asyncio.to_thread(self._client.download, image)

    async def save(self, image: ImageLike, path: Union[str, Path]) -> Path:
        """Download a render and write it to a local file."""
        return await asyncio.to_thread(self._client.save, image, path)

    async def __aenter__(self) -> AsyncHtml2img:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        return None

    def __repr__(self) -> str:
        return f"AsyncHtml2img(base_url={self.base_url!r}, timeout={self.timeout!r})"
