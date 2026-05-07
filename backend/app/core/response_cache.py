from copy import deepcopy
from time import monotonic
from typing import TypeVar

T = TypeVar("T")

_cache: dict[str, tuple[float, object]] = {}


def get_cached(key: str, *, ttl_seconds: float) -> T | None:
    cached = _cache.get(key)
    if cached is None:
        return None
    stored_at, value = cached
    if monotonic() - stored_at > ttl_seconds:
        _cache.pop(key, None)
        return None
    return deepcopy(value)  # type: ignore[return-value]


def set_cached(key: str, value: object) -> None:
    _cache[key] = (monotonic(), deepcopy(value))


def invalidate_cache_prefix(prefix: str) -> None:
    for key in list(_cache):
        if key.startswith(prefix):
            _cache.pop(key, None)
