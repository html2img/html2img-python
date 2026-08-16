"""Capture several URLs concurrently with the asyncio client.

    HTML2IMG_API_KEY=your-key python examples/batch_screenshots.py

Uses one credit per URL. https://html2img.com/screenshot-api/
"""

from __future__ import annotations

import asyncio

from html2img import AsyncHtml2img, Html2imgError

URLS = [
    "https://html2img.com",
    "https://html2img.com/screenshot-api/",
    "https://html2img.com/html-to-pdf/",
]


async def capture(client: AsyncHtml2img, url: str) -> None:
    try:
        response = await client.screenshot(url, width=1280, height=800, dpi=2)
    except Html2imgError as error:
        print(f"{url}: failed ({error})")
        return

    print(f"{url}: {response.url}")


async def main() -> None:
    async with AsyncHtml2img() as client:
        await asyncio.gather(*(capture(client, url) for url in URLS))


if __name__ == "__main__":
    asyncio.run(main())
