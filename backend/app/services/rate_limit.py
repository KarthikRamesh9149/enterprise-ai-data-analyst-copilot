from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import settings

_buckets: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(key_prefix: str):
    def dependency(request: Request):
        identifier = request.client.host if request.client else "local"
        key = f"{key_prefix}:{identifier}"
        now = time.time()
        bucket = _buckets[key]
        while bucket and bucket[0] < now - 60:
            bucket.popleft()
        if len(bucket) >= settings.rate_limit_per_minute:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
        bucket.append(now)

    return dependency
