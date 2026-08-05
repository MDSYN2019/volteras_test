from app.services.read_cache import TTLCache


def test_ttl_cache_reuses_common_read_until_cleared():
    cache = TTLCache(ttl_seconds=30)
    calls = 0

    def factory() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"calls": calls}

    assert cache.get_or_set("vehicle-page", factory) == {"calls": 1}
    assert cache.get_or_set("vehicle-page", factory) == {"calls": 1}
    assert calls == 1

    cache.clear()

    assert cache.get_or_set("vehicle-page", factory) == {"calls": 2}


def test_ttl_cache_can_be_disabled():
    cache = TTLCache(ttl_seconds=0)
    calls = 0

    def factory() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert cache.get_or_set("vehicle-page", factory) == 1
    assert cache.get_or_set("vehicle-page", factory) == 2
