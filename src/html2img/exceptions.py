"""Exception hierarchy for the html2img client.

Every request-time failure surfaces as an :class:`Html2imgError` or one of its
subclasses, so catching that single type is enough to handle anything the SDK
raises once a request is underway. Invalid arguments are reported before any
request is sent, as a plain :class:`ValueError` or :class:`TypeError`.

The names mirror the official PHP and JavaScript SDKs. ``ConnectionError`` and
``TimeoutError`` share a name with the built-ins of the same name; both are
strict subclasses of those built-ins, so an ``except TimeoutError`` written
against the built-in still catches ours.
"""

from __future__ import annotations

import builtins
from typing import Any, Dict, List, Mapping, Optional

__all__ = [
    "AuthenticationError",
    "ConnectionError",
    "Html2imgError",
    "InsufficientCreditsError",
    "NotFoundError",
    "NotSubscribedError",
    "RateLimitError",
    "ServerError",
    "TimeoutError",
    "ValidationError",
]


class Html2imgError(Exception):
    """Base type for every error raised by the client at request time.

    Catching this single type is enough to handle any failure originating from
    the SDK. No raw ``urllib`` error is ever allowed to escape the public API.

    :param message: Human-readable error message.
    :param status_code: The HTTP status code, when the failure came from a response.
    :param payload: The decoded JSON response body, when available.
    :param error_code: The machine-readable ``code`` field from the API body, when present.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        payload: Optional[Mapping[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload: Dict[str, Any] = dict(payload or {})
        self.error_code = error_code

    def __str__(self) -> str:
        if self.error_code:
            return f"{self.message} ({self.error_code})"

        return self.message

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}({self.message!r}, status_code={self.status_code!r}, "
            f"error_code={self.error_code!r})"
        )


class AuthenticationError(Html2imgError):
    """Raised on a 401 response: the API key is missing or not recognised.

    The API ``code`` is ``missing_api_key`` or ``invalid_api_key``.
    """


class InsufficientCreditsError(Html2imgError):
    """Raised on a 402 response: authenticated, but out of credits.

    The API ``code`` is ``insufficient_credits``.
    """

    @property
    def credits_remaining(self) -> Optional[int]:
        """Credits left on the account, as reported by the API. Zero on a 402."""
        value = self.payload.get("credits_remaining")

        return value if isinstance(value, int) and not isinstance(value, bool) else None


class NotSubscribedError(Html2imgError):
    """Raised on a 403 response: the key is valid but there is no active subscription.

    The API ``code`` is ``not_subscribed``.
    """


class NotFoundError(Html2imgError):
    """Raised on a 404 response, for example when a template slug does not exist.

    The API ``code`` is ``template_not_found``.
    """


class ValidationError(Html2imgError):
    """Raised on a 400 or 422 response when one or more request fields fail validation.

    The API ``code`` is ``validation_error``. :attr:`details` holds the
    per-field messages returned by the API.
    """

    def __init__(
        self,
        message: str,
        *,
        details: Optional[Mapping[str, List[str]]] = None,
        status_code: Optional[int] = None,
        payload: Optional[Mapping[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            status_code=status_code,
            payload=payload,
            error_code=error_code,
        )
        self.details: Dict[str, List[str]] = {k: list(v) for k, v in (details or {}).items()}


class RateLimitError(Html2imgError):
    """Raised on a 429 response: too many requests, or a plan quota was exceeded."""

    @property
    def retry_after(self) -> Optional[int]:
        """Seconds to wait before retrying, when the API supplies it."""
        value = self.payload.get("retry_after")

        return value if isinstance(value, int) and not isinstance(value, bool) else None


class TimeoutError(Html2imgError, builtins.TimeoutError):
    """Raised on a 408 or 504 response, or when the local timeout elapses.

    The API ``code`` is ``timeout_error`` or ``api_timeout_error``. For captures
    that routinely take this long, pass a ``webhook_url`` on the request to
    switch to asynchronous delivery.

    Subclasses the built-in :class:`TimeoutError`, so code catching that still
    catches this.
    """


class ServerError(Html2imgError):
    """Raised on a 5xx response when the renderer returns an unexpected error.

    The API ``code`` is ``service_error``. Retry once; if it persists, contact
    support with the ``id`` from the payload.
    """


class ConnectionError(Html2imgError, builtins.ConnectionError):
    """Raised when the request never reaches a response.

    DNS failure, refused connection, TLS error or a transport-level timeout.
    Subclasses the built-in :class:`ConnectionError`, so code catching that
    still catches this.
    """
