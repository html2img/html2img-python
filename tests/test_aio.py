"""The asyncio client mirrors the synchronous one."""

from __future__ import annotations

import pytest

from html2img import AsyncHtml2img, AuthenticationError
from tests.conftest import API_KEY, FakeTransport


@pytest.fixture
def async_client(transport: FakeTransport) -> AsyncHtml2img:
    return AsyncHtml2img(API_KEY, transport=transport)


async def test_it_renders_html(async_client: AsyncHtml2img, transport: FakeTransport) -> None:
    response = await async_client.html("<h1>Hi</h1>", width=1200)

    assert response.url == "https://i.html2img.com/abc123.png"
    assert transport.last["url"].endswith("/api/html")
    assert transport.last["body"] == {"html": "<h1>Hi</h1>", "width": 1200}


async def test_it_captures_a_screenshot(
    async_client: AsyncHtml2img, transport: FakeTransport
) -> None:
    await async_client.screenshot("https://example.com")

    assert transport.last["url"].endswith("/api/screenshot")


async def test_it_renders_a_template(async_client: AsyncHtml2img, transport: FakeTransport) -> None:
    await async_client.template("invoice-image", {"number": 7})

    assert transport.last["url"].endswith("/api/v1/templates/invoice-image")
    assert transport.last["body"] == {"number": 7}


async def test_it_saves_a_render(async_client: AsyncHtml2img, transport: FakeTransport, tmp_path):
    response = await async_client.html("<h1>Hi</h1>")
    transport.queued = [(200, b"png")]

    path = await async_client.save(response, tmp_path / "card.png")

    assert path.read_bytes() == b"png"


async def test_it_raises_the_same_typed_errors() -> None:
    client = AsyncHtml2img(API_KEY, transport=FakeTransport((401, {"error": "nope"})))

    with pytest.raises(AuthenticationError):
        await client.html("<h1>Hi</h1>")


async def test_it_works_as_an_async_context_manager(transport: FakeTransport) -> None:
    async with AsyncHtml2img(API_KEY, transport=transport) as client:
        assert (await client.html("<h1>Hi</h1>")).success is True
