"""Request validation, body building and response parsing."""

from __future__ import annotations

import pytest

from html2img import Format, HtmlRequest, RenderResponse, ScreenshotRequest


class TestHtmlRequest:
    def test_it_omits_unset_options(self) -> None:
        assert HtmlRequest(html="<h1>Hi</h1>").to_dict() == {"html": "<h1>Hi</h1>"}

    def test_it_maps_options_to_snake_case_api_fields(self) -> None:
        body = HtmlRequest(
            html="<h1>Hi</h1>",
            webhook_url="https://example.test/hook",
            ms_delay=100,
            wait_for_selector=".ready",
        ).to_dict()

        assert body["webhook_url"] == "https://example.test/hook"
        assert body["ms_delay"] == 100
        assert body["wait_for_selector"] == ".ready"

    def test_it_keeps_a_false_flag(self) -> None:
        assert HtmlRequest(html="<h1>Hi</h1>", fullpage=False).to_dict()["fullpage"] is False

    def test_it_rejects_an_empty_document(self) -> None:
        with pytest.raises(ValueError, match="html must not be empty"):
            HtmlRequest(html="")

    def test_it_rejects_a_non_string_document(self) -> None:
        with pytest.raises(TypeError, match="html must be a string"):
            HtmlRequest(html=123)  # type: ignore[arg-type]

    @pytest.mark.parametrize("value", [0, 5001])
    def test_it_rejects_out_of_range_dimensions(self, value: int) -> None:
        with pytest.raises(ValueError, match="between 1 and 5000"):
            HtmlRequest(html="<h1>Hi</h1>", width=value)

    @pytest.mark.parametrize("value", [0, 5])
    def test_it_rejects_an_out_of_range_dpi(self, value: int) -> None:
        with pytest.raises(ValueError, match="between 1 and 4"):
            HtmlRequest(html="<h1>Hi</h1>", dpi=value)

    @pytest.mark.parametrize("value", [0, 5001])
    def test_it_rejects_an_out_of_range_delay(self, value: int) -> None:
        with pytest.raises(ValueError, match="between 1 and 5000"):
            HtmlRequest(html="<h1>Hi</h1>", ms_delay=value)

    def test_it_accepts_a_format_as_a_string_or_enum(self) -> None:
        assert HtmlRequest(html="x", format="pdf").to_dict()["format"] == "pdf"
        assert HtmlRequest(html="x", format=Format.PDF).to_dict()["format"] == "pdf"
        assert HtmlRequest(html="x", format="PDF").to_dict()["format"] == "pdf"

    def test_it_rejects_an_unknown_format(self) -> None:
        with pytest.raises(ValueError, match="must be one of"):
            HtmlRequest(html="x", format="webp")


class TestScreenshotRequest:
    def test_it_omits_unset_options(self) -> None:
        assert ScreenshotRequest(url="https://example.com").to_dict() == {
            "url": "https://example.com"
        }

    def test_it_carries_the_selector(self) -> None:
        body = ScreenshotRequest(url="https://example.com", selector="#hero").to_dict()

        assert body["selector"] == "#hero"

    def test_it_rejects_an_empty_url(self) -> None:
        with pytest.raises(ValueError, match="url must not be empty"):
            ScreenshotRequest(url="")


class TestRenderResponse:
    def test_it_parses_a_synchronous_envelope(self) -> None:
        response = RenderResponse.from_dict(
            {
                "success": True,
                "id": "abc123",
                "url": "https://i.html2img.com/abc123.png",
                "expires_at": "2026-08-23T10:00:00Z",
                "credits_remaining": 49,
            }
        )

        assert response.success is True
        assert response.id == "abc123"
        assert response.url == "https://i.html2img.com/abc123.png"
        assert response.expires_at == "2026-08-23T10:00:00Z"
        assert response.credits_remaining == 49
        assert response.is_processing is False

    def test_it_parses_an_async_acceptance_envelope(self) -> None:
        response = RenderResponse.from_dict({"success": True, "status": "processing"})

        assert response.is_processing is True
        assert response.url is None

    def test_it_keeps_the_raw_payload(self) -> None:
        response = RenderResponse.from_dict({"success": True, "extra": {"nested": 1}})

        assert response.raw["extra"] == {"nested": 1}

    def test_it_tolerates_an_empty_payload(self) -> None:
        response = RenderResponse.from_dict({})

        assert response.success is False
        assert response.url is None
        assert response.credits_remaining is None

    def test_it_detects_a_pdf_render(self) -> None:
        assert RenderResponse.from_dict({"url": "https://i.html2img.com/a.pdf"}).is_pdf is True
        assert RenderResponse.from_dict({"url": "https://i.html2img.com/a.png"}).is_pdf is False

    def test_it_stringifies_to_its_url(self) -> None:
        assert str(RenderResponse.from_dict({"url": "https://i.html2img.com/a.png"})) == (
            "https://i.html2img.com/a.png"
        )
