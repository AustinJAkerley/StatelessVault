"""Errors, kept plain and honest.

An error here is a signpost, not a lecture. Each one carries a short machine
code that programs read and a human message that people read. The codes never
change on a whim, because other people's code leans on them. The messages are
free to speak like a person.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ApiError(Exception):
    error: str
    message: str
    status_code: int = 400


class RateLimitError(ApiError):
    def __init__(self) -> None:
        super().__init__(
            error="rate_limited",
            message="You are asking too fast. The vault is not going anywhere. Wait a moment and come back.",
            status_code=429,
        )


def error_response_payload(error: ApiError) -> dict[str, str]:
    return {"error": error.error, "message": error.message}
