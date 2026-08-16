"""HTTP transport for the client.

The default transport is built on :mod:`urllib.request` from the standard
library, so the package has no runtime dependencies. Anything callable with the
same signature can be passed to :class:`~html2img.client.Html2img` as
``transport=``, which is the seam for wiring in ``requests``, ``httpx``, a
proxy, retry middleware, or a stub in your tests.

A transport returns the raw ``(status_code, body)`` pair for *any* HTTP
response, including 4xx and 5xx. Mapping a status onto a typed exception is the
client's job. A transport only raises when no response was received at all.
"""

from __future__ import annotations

import socket
import urllib.error
import urllib.request
from typing import Mapping, Optional, Tuple

from html2img._version import __version__
from html2img.exceptions import ConnectionError, TimeoutError

try:  # pragma: no cover - typing only
    from typing import Protocol
except ImportError:  # pragma: no cover - Python < 3.8
    Protocol = object  # type: ignore[assignment,misc]

__all__ = ["USER_AGENT", "Transport", "UrllibTransport"]

USER_AGENT = f"html2img-python/{__version__}"


class Transport(Protocol):  # pragma: no cover - structural type
    """The callable interface a transport must satisfy.

    :param method: The HTTP method, ``"POST"`` or ``"GET"``.
    :param url: The absolute URL to request.
    :param headers: Headers to send.
    :param body: The request body, or ``None`` for a bodyless request.
    :param timeout: Timeout in seconds for the whole request.
    :returns: ``(status_code, body_bytes)``.
    """

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Optional[bytes],
        timeout: float,
    ) -> Tuple[int, bytes]: ...


class UrllibTransport:
    """The default transport, backed by :mod:`urllib.request`.

    Stateless and thread-safe: a single instance can be shared by any number of
    clients and threads.
    """

    def __call__(
        self,
        *,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Optional[bytes],
        timeout: float,
    ) -> Tuple[int, bytes]:
        request = urllib.request.Request(url=url, data=body, method=method)

        for name, value in headers.items():
            request.add_header(name, value)

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return int(response.status), response.read()
        except urllib.error.HTTPError as error:
            # A 4xx or 5xx is still a response; hand it back for mapping.
            with error:
                return int(error.code), error.read()
        except socket.timeout as error:
            raise TimeoutError(
                f"The request to {url} timed out after {timeout:g} seconds."
            ) from error
        except urllib.error.URLError as error:
            reason = error.reason

            if isinstance(reason, socket.timeout):
                raise TimeoutError(
                    f"The request to {url} timed out after {timeout:g} seconds."
                ) from error

            raise ConnectionError(f"Could not reach the html2img API: {reason}") from error
        except OSError as error:  # pragma: no cover - defensive
            raise ConnectionError(f"Could not reach the html2img API: {error}") from error
