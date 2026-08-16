"""Mapping of API responses and transport failures onto typed exceptions."""

from __future__ import annotations

import socket
import urllib.error
from typing import Any, Type

import pytest

from html2img import (
    AuthenticationError,
    ConnectionError,
    Html2img,
    Html2imgError,
    InsufficientCreditsError,
    NotFoundError,
    NotSubscribedError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from html2img.transport import UrllibTransport
from tests.conftest import API_KEY, FakeTransport


def client_for(status: int, payload: Any) -> Html2img:
    return Html2img(API_KEY, transport=FakeTransport((status, payload)))


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (402, InsufficientCreditsError),
        (403, NotSubscribedError),
        (404, NotFoundError),
        (408, TimeoutError),
        (422, ValidationError),
        (429, RateLimitError),
        (418, Html2imgError),
        (500, ServerError),
        (503, ServerError),
        (504, TimeoutError),
    ],
)
def test_it_maps_status_codes_onto_exception_types(
    status: int, expected: Type[Html2imgError]
) -> None:
    with pytest.raises(expected):
        client_for(status, {"error": "nope"}).html("<h1>Hi</h1>")


def test_every_error_is_an_html2img_error() -> None:
    with pytest.raises(Html2imgError):
        client_for(401, {"error": "Invalid API key."}).html("<h1>Hi</h1>")


def test_it_surfaces_the_api_message_status_and_code() -> None:
    with pytest.raises(AuthenticationError) as caught:
        client_for(401, {"error": "Invalid API key.", "code": "invalid_api_key"}).html("x")

    error = caught.value

    assert error.message == "Invalid API key."
    assert error.status_code == 401
    assert error.error_code == "invalid_api_key"
    assert error.payload["code"] == "invalid_api_key"
    assert str(error) == "Invalid API key. (invalid_api_key)"


def test_it_falls_back_to_the_message_field() -> None:
    with pytest.raises(Html2imgError) as caught:
        client_for(500, {"message": "Renderer exploded."}).html("x")

    assert caught.value.message == "Renderer exploded."


def test_it_synthesises_a_message_when_the_body_is_empty() -> None:
    with pytest.raises(Html2imgError) as caught:
        client_for(500, {}).html("x")

    assert "HTTP 500" in caught.value.message


def test_it_tolerates_a_non_json_error_body() -> None:
    with pytest.raises(ServerError) as caught:
        Html2img(API_KEY, transport=FakeTransport((502, b"<html>bad gateway</html>"))).html("x")

    assert caught.value.status_code == 502


def test_validation_errors_carry_per_field_details() -> None:
    with pytest.raises(ValidationError) as caught:
        client_for(
            422,
            {
                "error": "The given data was invalid.",
                "code": "validation_error",
                "details": {"width": ["The width must be between 1 and 5000."], "html": "Required"},
            },
        ).html("x")

    assert caught.value.details == {
        "width": ["The width must be between 1 and 5000."],
        "html": ["Required"],
    }


def test_insufficient_credits_exposes_the_remaining_balance() -> None:
    with pytest.raises(InsufficientCreditsError) as caught:
        client_for(402, {"error": "Out of credits.", "credits_remaining": 0}).html("x")

    assert caught.value.credits_remaining == 0


def test_rate_limit_exposes_retry_after() -> None:
    with pytest.raises(RateLimitError) as caught:
        client_for(429, {"error": "Slow down.", "retry_after": 30}).html("x")

    assert caught.value.retry_after == 30


def test_our_timeout_error_is_catchable_as_the_builtin() -> None:
    with pytest.raises(BaseException) as caught:
        client_for(504, {"error": "Render timed out."}).html("x")

    assert isinstance(caught.value, TimeoutError)
    assert isinstance(caught.value, Html2imgError)


class TestUrllibTransport:
    def _transport_raising(self, error: BaseException, monkeypatch: pytest.MonkeyPatch) -> None:
        def boom(*args: Any, **kwargs: Any) -> Any:
            raise error

        monkeypatch.setattr("urllib.request.urlopen", boom)

    def test_a_refused_connection_becomes_a_connection_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._transport_raising(urllib.error.URLError("connection refused"), monkeypatch)

        with pytest.raises(ConnectionError, match="Could not reach"):
            Html2img(API_KEY, transport=UrllibTransport()).html("x")

    def test_a_socket_timeout_becomes_a_timeout_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._transport_raising(socket.timeout("timed out"), monkeypatch)

        with pytest.raises(TimeoutError, match="timed out after"):
            Html2img(API_KEY, transport=UrllibTransport()).html("x")

    def test_a_wrapped_socket_timeout_becomes_a_timeout_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._transport_raising(urllib.error.URLError(socket.timeout("timed out")), monkeypatch)

        with pytest.raises(TimeoutError):
            Html2img(API_KEY, transport=UrllibTransport()).html("x")

    def test_no_raw_urllib_error_escapes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._transport_raising(OSError("something low level"), monkeypatch)

        with pytest.raises(Html2imgError):
            Html2img(API_KEY, transport=UrllibTransport()).html("x")
