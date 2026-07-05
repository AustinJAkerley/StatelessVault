from app.rate_limiter import FixedWindowRateLimiter


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = FixedWindowRateLimiter(limit=2, window_seconds=60)

    assert limiter.allow_request() is True
    assert limiter.allow_request() is True
    assert limiter.allow_request() is False


def test_rate_limiter_resets_after_window(monkeypatch) -> None:
    now = [1_000.0]

    def fake_time() -> float:
        return now[0]

    monkeypatch.setattr("app.rate_limiter.time.time", fake_time)
    limiter = FixedWindowRateLimiter(limit=1, window_seconds=10)

    assert limiter.allow_request() is True
    assert limiter.allow_request() is False

    now[0] += 10.1

    assert limiter.allow_request() is True
