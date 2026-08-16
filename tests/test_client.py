"""Client configuration, endpoints and request bodies."""

from __future__ import annotations

import pytest

from html2img import Format, Html2img, HtmlRequest, ScreenshotRequest
from tests.conftest import API_KEY, FakeTransport


class TestConfiguration:
    def test_it_reads_the_api_key_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HTML2IMG_API_KEY", "from-env")

        assert Html2img()._api_key == "from-env"

    def test_an_explicit_key_wins_over_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HTML2IMG_API_KEY", "from-env")

        assert Html2img("explicit")._api_key == "explicit"

    def test_it_refuses_to_build_without_a_key(self) -> None:
        with pytest.raises(ValueError, match="HTML2IMG_API_KEY"):
            Html2img()

    def test_it_defaults_the_base_url_and_timeout(self) -> None:
        client = Html2img(API_KEY)

        assert client.base_url == "https://app.html2img.com"
        assert client.timeout == 35.0

    def test_it_reads_the_base_url_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HTML2IMG_BASE_URI", "https://example.test/")

        assert Html2img(API_KEY).base_url == "https://example.test"

    def test_it_trims_trailing_slashes_from_the_base_url(self) -> None:
        assert (
            Html2img(API_KEY, base_url="https://example.test//").base_url == "https://example.test"
        )

    def test_it_rejects_a_non_positive_timeout(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            Html2img(API_KEY, timeout=0)

    def test_it_works_as_a_context_manager(self, transport: FakeTransport) -> None:
        with Html2img(API_KEY, transport=transport) as client:
            assert client.html("<h1>Hi</h1>").url == "https://i.html2img.com/abc123.png"


class TestHtmlEndpoint:
    def test_it_posts_to_the_html_endpoint(
        self, client: Html2img, transport: FakeTransport
    ) -> None:
        client.html("<h1>Hi</h1>")

        assert transport.last["method"] == "POST"
        assert transport.last["url"] == "https://app.html2img.com/api/html"
        assert transport.last["body"] == {"html": "<h1>Hi</h1>"}

    def test_it_sends_the_authentication_and_content_headers(
        self, client: Html2img, transport: FakeTransport
    ) -> None:
        client.html("<h1>Hi</h1>")

        headers = transport.last["headers"]

        assert headers["X-API-Key"] == API_KEY
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"].startswith("html2img-python/")

    def test_it_passes_render_options_through(
        self, client: Html2img, transport: FakeTransport
    ) -> None:
        client.html(
            "<h1>Hi</h1>",
            css="body { margin: 0 }",
            width=1200,
            height=630,
            dpi=2,
            fullpage=True,
            ms_delay=250,
            wait_for_selector="#ready",
            webhook_url="https://example.test/hook",
            format="pdf",
            scale_to_fit=True,
        )

        assert transport.last["body"] == {
            "html": "<h1>Hi</h1>",
            "css": "body { margin: 0 }",
            "width": 1200,
            "height": 630,
            "dpi": 2,
            "fullpage": True,
            "ms_delay": 250,
            "wait_for_selector": "#ready",
            "webhook_url": "https://example.test/hook",
            "format": "pdf",
            "scale_to_fit": True,
        }

    def test_it_accepts_a_request_object(self, client: Html2img, transport: FakeTransport) -> None:
        client.html(HtmlRequest(html="<h1>Hi</h1>", width=800, format=Format.PDF))

        assert transport.last["body"] == {"html": "<h1>Hi</h1>", "width": 800, "format": "pdf"}

    def test_it_returns_a_parsed_response(self, client: Html2img) -> None:
        response = client.html("<h1>Hi</h1>")

        assert response.success is True
        assert response.id == "abc123"
        assert response.url == "https://i.html2img.com/abc123.png"
        assert response.credits_remaining == 49
        assert response.is_processing is False


class TestScreenshotEndpoint:
    def test_it_posts_to_the_screenshot_endpoint(
        self, client: Html2img, transport: FakeTransport
    ) -> None:
        client.screenshot("https://example.com", selector="#hero", fullpage=True)

        assert transport.last["url"] == "https://app.html2img.com/api/screenshot"
        assert transport.last["body"] == {
            "url": "https://example.com",
            "selector": "#hero",
            "fullpage": True,
        }

    def test_it_accepts_a_request_object(self, client: Html2img, transport: FakeTransport) -> None:
        client.screenshot(ScreenshotRequest(url="https://example.com", width=1200))

        assert transport.last["body"] == {"url": "https://example.com", "width": 1200}


class TestTemplateEndpoint:
    def test_it_posts_to_the_slugged_template_endpoint(
        self, client: Html2img, transport: FakeTransport
    ) -> None:
        client.template("invoice-image", {"number": 1042})

        assert transport.last["url"] == "https://app.html2img.com/api/v1/templates/invoice-image"
        assert transport.last["body"] == {"number": 1042}

    def test_it_merges_keyword_fields_over_the_data_mapping(
        self, client: Html2img, transport: FakeTransport
    ) -> None:
        client.template("invoice-image", {"number": 1, "amount": "1"}, amount="2")

        assert transport.last["body"] == {"number": 1, "amount": "2"}

    def test_it_url_encodes_the_slug(self, client: Html2img, transport: FakeTransport) -> None:
        client.template("weird/slug")

        assert transport.last["url"].endswith("/api/v1/templates/weird%2Fslug")

    def test_it_rejects_an_empty_slug(self, client: Html2img) -> None:
        with pytest.raises(ValueError, match="slug"):
            client.template("")


class TestDownloadAndSave:
    def test_it_downloads_the_rendered_bytes(self, client: Html2img) -> None:
        response = client.html("<h1>Hi</h1>")
        client._transport.queued = [(200, b"\x89PNG-bytes")]  # type: ignore[attr-defined]

        assert client.download(response) == b"\x89PNG-bytes"

    def test_it_downloads_from_a_plain_url(
        self, client: Html2img, transport: FakeTransport
    ) -> None:
        transport.queued = [(200, b"bytes")]

        assert client.download("https://i.html2img.com/x.png") == b"bytes"
        assert transport.last["method"] == "GET"
        assert transport.last["url"] == "https://i.html2img.com/x.png"

    def test_it_saves_a_render_to_disk(self, client: Html2img, tmp_path) -> None:
        response = client.html("<h1>Hi</h1>")
        client._transport.queued = [(200, b"png")]  # type: ignore[attr-defined]

        path = client.save(response, tmp_path / "nested" / "card.png")

        assert path.read_bytes() == b"png"

    def test_it_refuses_to_download_a_processing_render(self, client: Html2img) -> None:
        from html2img import Html2imgError, RenderResponse

        with pytest.raises(Html2imgError, match="no image URL yet"):
            client.download(RenderResponse(success=True, status="processing"))
