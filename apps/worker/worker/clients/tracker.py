from __future__ import annotations

from datetime import datetime

from redis import Redis
from redis.exceptions import RedisError


class TrackerStore:
    def __init__(self, client: Redis | None) -> None:
        self.client = client

    @classmethod
    def from_url(cls, redis_url: str) -> "TrackerStore":
        try:
            client = Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            return cls(client)
        except RedisError:
            return cls(None)

    def record(self, task_name: str, run_at: datetime) -> None:
        if self.client is None:
            return
        self.client.set(f"job_focus:worker:last_run:{task_name}", run_at.isoformat())
