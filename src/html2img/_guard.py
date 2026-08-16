"""Internal range checks shared by the request objects.

These mirror the server-side validation rules, so obvious mistakes fail fast
with a clear message before a request is sent (and before a credit is spent).
"""

from __future__ import annotations

from typing import Optional

MIN_DIMENSION = 1
MAX_DIMENSION = 5000
MIN_DPI = 1
MAX_DPI = 4
MIN_MS_DELAY = 1
MAX_MS_DELAY = 5000


def required_string(name: str, value: object) -> str:
    """Require a non-empty string."""
    if not isinstance(value, str):
        raise TypeError(f"The {name} must be a string, got {type(value).__name__}.")

    if value == "":
        raise ValueError(f"The {name} must not be empty.")

    return value


def optional_string(name: str, value: object) -> Optional[str]:
    """Allow ``None``, otherwise require a string."""
    if value is None:
        return None

    if not isinstance(value, str):
        raise TypeError(f"The {name} must be a string or None, got {type(value).__name__}.")

    return value


def optional_bool(name: str, value: object) -> Optional[bool]:
    """Allow ``None``, otherwise require a bool."""
    if value is None:
        return None

    if not isinstance(value, bool):
        raise TypeError(f"The {name} must be a bool or None, got {type(value).__name__}.")

    return value


def _optional_int_in_range(name: str, value: object, low: int, high: int) -> Optional[int]:
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"The {name} must be an int or None, got {type(value).__name__}.")

    if value < low or value > high:
        raise ValueError(f"The {name} must be between {low} and {high}, got {value}.")

    return value


def dimension(name: str, value: object) -> Optional[int]:
    """Validate a viewport dimension (width or height): 1 to 5000 pixels."""
    return _optional_int_in_range(name, value, MIN_DIMENSION, MAX_DIMENSION)


def dpi(value: object) -> Optional[int]:
    """Validate the device pixel ratio: 1 to 4."""
    return _optional_int_in_range("dpi", value, MIN_DPI, MAX_DPI)


def ms_delay(value: object) -> Optional[int]:
    """Validate the post-load delay: 1 to 5000 milliseconds."""
    return _optional_int_in_range("ms_delay", value, MIN_MS_DELAY, MAX_MS_DELAY)


def timeout(value: object) -> float:
    """Validate a request timeout: a positive number of seconds."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"The timeout must be a number, got {type(value).__name__}.")

    if value <= 0:
        raise ValueError(f"The timeout must be a positive number of seconds, got {value}.")

    return float(value)
