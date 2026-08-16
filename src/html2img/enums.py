"""Enumerations used by the request objects and the client."""

from __future__ import annotations

from enum import Enum

__all__ = ["Format"]


class Format(str, Enum):
    """Output format for a render.

    Defaults to PNG server-side when omitted from the request. ``Format`` is a
    ``str`` subclass, so ``Format.PDF == "pdf"`` and it serialises to JSON as
    the plain string.
    """

    PNG = "png"
    PDF = "pdf"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value

    @classmethod
    def coerce(cls, value: Format | str | None) -> Format | None:
        """Normalise a string or :class:`Format` into a :class:`Format`.

        :raises ValueError: if the value is not a supported format.
        """
        if value is None:
            return None

        if isinstance(value, cls):
            return value

        if isinstance(value, str):
            try:
                return cls(value.lower())
            except ValueError:
                pass

        supported = ", ".join(member.value for member in cls)

        raise ValueError(f"The format must be one of: {supported}. Got {value!r}.")
