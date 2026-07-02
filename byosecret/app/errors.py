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
            message="Global request limit exceeded. Try again later.",
            status_code=429,
        )


def error_response_payload(error: ApiError) -> dict[str, str]:
    return {"error": error.error, "message": error.message}
