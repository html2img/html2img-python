"""Shared test fixtures.

Every test drives the client through a fake transport, so the suite never
touches the network and never spends a credit.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Optional, Tuple

import pytest

from html2img import Html2img

API_KEY = "test-key"


class FakeTransport:
    """A transport that records calls and replays queued responses."""

    def __init__(self, *responses: Tuple[int, Any]) -> None:
        self.queued: List[Tuple[int, Any]] = list(responses) or [(200, {"success": True})]
        self.calls: List[Dict[str, Any]] = []

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Optional[bytes],
        timeout: float,
    ) -> Tuple[int, bytes]:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": dict(headers),
                "body": json.loads(body.decode("utf-8")) if body else None,
                "timeout": timeout,
            }
        )

        status, payload = self.queued.pop(0) if len(self.queued) > 1 else self.queued[0]

        if isinstance(payload, bytes):
            return status, payload

        return status, json.dumps(payload).encode("utf-8")

    @property
    def last(self) -> Dict[str, Any]:
        return self.calls[-1]


@pytest.fixture
def transport() -> FakeTransport:
    return FakeTransport(
        (
            200,
            {
                "success": True,
                "id": "abc123",
                "url": "https://i.html2img.com/abc123.png",
                "credits_remaining": 49,
            },
        )
    )


@pytest.fixture
def client(transport: FakeTransport) -> Html2img:
    return Html2img(API_KEY, transport=transport)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HTML2IMG_API_KEY", raising=False)
    monkeypatch.delenv("HTML2IMG_BASE_URI", raising=False)
