"""Tests for the async pagination helper."""

from __future__ import annotations

import pytest

from gitforge.pagination import paginate
from gitforge.types import PaginatedResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_fetcher(pages: list[PaginatedResponse]):
    """Return an async fetcher that serves pre-built pages keyed by offset."""
    call_log: list[tuple[int, int]] = []

    async def fetcher(limit: int, offset: int) -> PaginatedResponse:
        call_log.append((limit, offset))
        for page in pages:
            if page.offset == offset:
                return page
        # If no matching page found, return empty
        return PaginatedResponse(data=[], total=0, limit=limit, offset=offset, has_more=False)

    fetcher.call_log = call_log  # type: ignore[attr-defined]
    return fetcher


async def collect(gen) -> list:
    """Drain an async generator into a list."""
    items = []
    async for item in gen:
        items.append(item)
    return items


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPaginateSinglePage:
    """Yields all items from a single page when has_more is False."""

    async def test_returns_all_items(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=["a", "b", "c"], total=3, limit=20, offset=0, has_more=False),
        ])

        items = await collect(paginate(fetcher))

        assert items == ["a", "b", "c"]

    async def test_fetcher_called_once(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=["a", "b"], total=2, limit=20, offset=0, has_more=False),
        ])

        await collect(paginate(fetcher))

        assert len(fetcher.call_log) == 1
        assert fetcher.call_log[0] == (20, 0)


class TestPaginateMultiplePages:
    """Fetches multiple pages until has_more is False."""

    async def test_two_pages(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[1, 2, 3], total=5, limit=3, offset=0, has_more=True),
            PaginatedResponse(data=[4, 5], total=5, limit=3, offset=3, has_more=False),
        ])

        items = await collect(paginate(fetcher, page_size=3))

        assert items == [1, 2, 3, 4, 5]

    async def test_three_pages(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=["x"], total=3, limit=1, offset=0, has_more=True),
            PaginatedResponse(data=["y"], total=3, limit=1, offset=1, has_more=True),
            PaginatedResponse(data=["z"], total=3, limit=1, offset=2, has_more=False),
        ])

        items = await collect(paginate(fetcher, page_size=1))

        assert items == ["x", "y", "z"]

    async def test_passes_correct_offset_to_fetcher(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[1, 2], total=4, limit=2, offset=0, has_more=True),
            PaginatedResponse(data=[3, 4], total=4, limit=2, offset=2, has_more=False),
        ])

        await collect(paginate(fetcher, page_size=2))

        assert fetcher.call_log == [(2, 0), (2, 2)]


class TestPaginateMaxItems:
    """Respects max_items limit, stopping early even if more data is available."""

    async def test_stops_at_max_items_within_page(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[1, 2, 3, 4, 5], total=5, limit=20, offset=0, has_more=False),
        ])

        items = await collect(paginate(fetcher, max_items=3))

        assert items == [1, 2, 3]

    async def test_stops_at_max_items_across_pages(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[1, 2], total=6, limit=2, offset=0, has_more=True),
            PaginatedResponse(data=[3, 4], total=6, limit=2, offset=2, has_more=True),
            PaginatedResponse(data=[5, 6], total=6, limit=2, offset=4, has_more=False),
        ])

        items = await collect(paginate(fetcher, page_size=2, max_items=3))

        assert items == [1, 2, 3]

    async def test_does_not_fetch_beyond_needed_pages(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[1, 2], total=6, limit=2, offset=0, has_more=True),
            PaginatedResponse(data=[3, 4], total=6, limit=2, offset=2, has_more=True),
            PaginatedResponse(data=[5, 6], total=6, limit=2, offset=4, has_more=False),
        ])

        await collect(paginate(fetcher, page_size=2, max_items=3))

        # Should only need first two pages (items 1,2 from page 1, item 3 from page 2)
        assert len(fetcher.call_log) == 2

    async def test_max_items_zero_yields_nothing(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[1, 2, 3], total=3, limit=20, offset=0, has_more=False),
        ])

        items = await collect(paginate(fetcher, max_items=0))

        assert items == []


class TestPaginateEmptyPage:
    """Handles empty first page by returning nothing."""

    async def test_empty_data_returns_nothing(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[], total=0, limit=20, offset=0, has_more=False),
        ])

        items = await collect(paginate(fetcher))

        assert items == []

    async def test_empty_data_with_has_more_false(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[], total=0, limit=20, offset=0, has_more=False),
        ])

        items = await collect(paginate(fetcher))

        assert items == []
        assert len(fetcher.call_log) == 1


class TestPaginatePageSize:
    """Verifies custom page_size is forwarded to the fetcher."""

    async def test_custom_page_size(self):
        fetcher = make_fetcher([
            PaginatedResponse(data=[1], total=1, limit=50, offset=0, has_more=False),
        ])

        await collect(paginate(fetcher, page_size=50))

        assert fetcher.call_log[0][0] == 50
