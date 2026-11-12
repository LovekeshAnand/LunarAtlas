import asyncio

from fastapi import HTTPException

from app.api.v1 import endpoints
from app.cache.redis_cache import CacheLayer


class FakeRedis:
    def __init__(self, keys):
        self.keys = set(keys)

    async def scan_iter(self, match):
        import fnmatch
        for k in [k for k in self.keys if fnmatch.fnmatch(k, match)]:
            yield k

    async def delete(self, key):
        self.keys.discard(key)


def test_clear_pattern_removes_written_keys():
    c = CacheLayer()
    key = c.generate_key("spectrum", "x")
    c.redis = FakeRedis({key, "other:1"})
    asyncio.run(c.clear_pattern("*"))
    assert c.redis.keys == {"other:1"}


def test_clear_cache_requires_token(monkeypatch):
    monkeypatch.setattr(endpoints.settings, "CACHE_CLEAR_TOKEN", "s3cret")
    for token in (None, "wrong"):
        try:
            asyncio.run(endpoints.clear_cache(pattern="*", x_admin_token=token))
            raise AssertionError("accepted bad token")
        except HTTPException as e:
            assert e.status_code == 403
    monkeypatch.setattr(endpoints.settings, "CACHE_CLEAR_TOKEN", None)
    try:
        asyncio.run(endpoints.clear_cache(pattern="*", x_admin_token="anything"))
        raise AssertionError("endpoint not disabled")
    except HTTPException as e:
        assert e.status_code == 403
