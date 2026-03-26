from __future__ import annotations

from typing import AsyncGenerator, Awaitable, Callable, Optional, TypeVar

from .types import PaginatedResponse

T = TypeVar("T")

PageFetcher = Callable[[int, int], Awaitable[PaginatedResponse]]


async def paginate(
    fetcher: PageFetcher,
    page_size: int = 20,
    max_items: Optional[int] = None,
) -> AsyncGenerator:
    """Async generator that auto-paginates through a list endpoint.

    Usage::

        async for repo in paginate(
            lambda l, o: client.repos.list(limit=l, offset=o)
        ):
            print(repo.name)
    """
    offset = 0
    yielded = 0
    limit = max_items if max_items is not None else float("inf")

    while True:
        page = await fetcher(page_size, offset)

        for item in page.data:
            if yielded >= limit:
                return
            yield item
            yielded += 1

        if not page.has_more or not page.data:
            return
        offset += len(page.data)
