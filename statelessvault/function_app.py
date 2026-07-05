from __future__ import annotations

import json

import azure.functions as func

from app.crypto_service import CryptoService
from app.errors import ApiError, RateLimitError, error_response_payload
from app.models import parse_decrypt_request, parse_encrypt_request
from app.rate_limiter import FixedWindowRateLimiter

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
rate_limiter = FixedWindowRateLimiter(limit=10_000, window_seconds=60)


def _json_response(payload: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps(payload),
        status_code=status_code,
        mimetype="application/json",
    )


def _parse_json_request(req: func.HttpRequest) -> dict:
    try:
        body = req.get_json()
    except ValueError as exc:
        raise ApiError("malformed_json", "Request body must be valid JSON.", 400) from exc

    if not isinstance(body, dict):
        raise ApiError("malformed_json", "Request body must be a JSON object.", 400)

    return body


def _guard_rate_limit() -> None:
    if not rate_limiter.allow_request():
        raise RateLimitError()


@app.route(route="encrypt", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def encrypt(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _guard_rate_limit()
        payload = _parse_json_request(req)
        request_model = parse_encrypt_request(payload)
        response = CryptoService.encrypt(
            plaintext=request_model.plaintext,
            secret=request_model.secret,
        )
        return _json_response(response, status_code=200)
    except ApiError as error:
        return _json_response(error_response_payload(error), status_code=error.status_code)


@app.route(route="decrypt", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def decrypt(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _guard_rate_limit()
        payload = _parse_json_request(req)
        request_model = parse_decrypt_request(payload)
        plaintext = CryptoService.decrypt(
            secret=request_model.secret,
            salt=request_model.salt,
            nonce=request_model.nonce,
            ciphertext=request_model.ciphertext,
            tag=request_model.tag,
        )
        return _json_response({"plaintext": plaintext}, status_code=200)
    except ApiError as error:
        return _json_response(error_response_payload(error), status_code=error.status_code)
