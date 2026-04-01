from __future__ import annotations

import asyncio
from typing import Any, Optional

from ..http import HttpClient


class JobsResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def list(
        self,
        status: Optional[str] = None,
        type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> dict:
        query: dict[str, str] = {}
        if status is not None:
            query["status"] = status
        if type is not None:
            query["type"] = type
        if limit is not None:
            query["limit"] = str(limit)
        if offset is not None:
            query["offset"] = str(offset)
        return await self._http.get("/jobs", query)

    async def get(self, job_id: str) -> dict:
        return await self._http.get(f"/jobs/{job_id}")

    async def cancel(self, job_id: str) -> dict:
        return await self._http.delete_with_body(f"/jobs/{job_id}")

    async def wait_for(
        self,
        job_id: str,
        poll_interval_s: float = 2.0,
        timeout_s: float = 300.0,
    ) -> dict:
        import time

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            job = await self.get(job_id)
            if job.get("status") in ("completed", "failed", "cancelled"):
                return job
            await asyncio.sleep(poll_interval_s)
        raise TimeoutError(f"Job {job_id} did not complete within {timeout_s}s")
