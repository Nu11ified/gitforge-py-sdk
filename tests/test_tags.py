from __future__ import annotations

import json
from urllib.parse import quote

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.tags import TagsResource
from gitforge.types import Tag, PaginatedResponse


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"
BASE_URL = "https://api.gitforge.dev"
TAGS_URL = f"{BASE_URL}/repos/{REPO_ID}/tags"

TAG_JSON = {
    "name": "v1.0.0",
    "sha": "abc123def456789",
}


def _tag_json(**overrides: object) -> dict:
    d = dict(TAG_JSON)
    d.update(overrides)
    return d


def _paginated(tags: list[dict], **overrides: object) -> dict:
    d: dict = {
        "data": tags,
        "total": len(tags),
        "limit": 50,
        "offset": 0,
        "hasMore": False,
    }
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tags(http_client: HttpClient) -> TagsResource:
    return TagsResource(http_client, REPO_ID)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    async def test_lists_tags_with_default_params(
        self, tags: TagsResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = _paginated([TAG_JSON])
        route = mock_router.get(TAGS_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await tags.list()
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"
        url_str = str(request.url)
        assert "limit=" not in url_str
        assert "offset=" not in url_str

    async def test_passes_limit_and_offset(
        self, tags: TagsResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = _paginated(
            [TAG_JSON], total=100, limit=10, offset=20, hasMore=True
        )
        route = mock_router.get(TAGS_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await tags.list(limit=10, offset=20)
        url_str = str(route.calls[0].request.url)
        assert "limit=10" in url_str
        assert "offset=20" in url_str
        assert result.limit == 10
        assert result.offset == 20
        assert result.has_more is True

    async def test_returns_paginated_response_with_tag_objects(
        self, tags: TagsResource, mock_router: respx.MockRouter
    ) -> None:
        t1 = _tag_json(name="v1.0.0", sha="aaa111")
        t2 = _tag_json(name="v2.0.0", sha="bbb222")
        paginated = _paginated([t1, t2], total=2)
        mock_router.get(TAGS_URL).mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await tags.list()
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 2
        assert all(isinstance(t, Tag) for t in result.data)
        assert result.data[0].name == "v1.0.0"
        assert result.data[0].sha == "aaa111"
        assert result.data[1].name == "v2.0.0"
        assert result.data[1].sha == "bbb222"
        assert result.total == 2
        assert result.has_more is False


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_creates_tag_with_name_and_sha(
        self, tags: TagsResource, mock_router: respx.MockRouter
    ) -> None:
        tag_data = _tag_json(name="v1.0.0", sha="def456abc789")
        route = mock_router.post(TAGS_URL).mock(
            return_value=httpx.Response(200, json=tag_data)
        )
        result = await tags.create("v1.0.0", sha="def456abc789")
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {"name": "v1.0.0", "sha": "def456abc789"}
        assert isinstance(result, Tag)
        assert result.name == "v1.0.0"
        assert result.sha == "def456abc789"

    async def test_returns_tag_dataclass(
        self, tags: TagsResource, mock_router: respx.MockRouter
    ) -> None:
        tag_data = _tag_json(name="release-v3", sha="deadbeef12345678")
        mock_router.post(TAGS_URL).mock(
            return_value=httpx.Response(200, json=tag_data)
        )
        result = await tags.create("release-v3", sha="deadbeef12345678")
        assert isinstance(result, Tag)
        assert result.name == "release-v3"
        assert result.sha == "deadbeef12345678"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_deletes_tag_by_name(
        self, tags: TagsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(f"{TAGS_URL}/v1.0.0").mock(
            return_value=httpx.Response(204)
        )
        result = await tags.delete("v1.0.0")
        assert route.called
        assert route.calls[0].request.method == "DELETE"
        assert result is None

    async def test_url_encodes_slash_in_tag_name(
        self, tags: TagsResource, mock_router: respx.MockRouter
    ) -> None:
        encoded = quote("release/v1", safe="")
        route = mock_router.delete(f"{TAGS_URL}/{encoded}").mock(
            return_value=httpx.Response(204)
        )
        await tags.delete("release/v1")
        request_url = str(route.calls[0].request.url)
        # The slash must be encoded as %2F
        assert "/tags/release%2Fv1" in request_url

    async def test_url_encodes_multiple_special_chars(
        self, tags: TagsResource, mock_router: respx.MockRouter
    ) -> None:
        tag_name = "feat/foo bar+baz"
        encoded = quote(tag_name, safe="")
        route = mock_router.delete(f"{TAGS_URL}/{encoded}").mock(
            return_value=httpx.Response(204)
        )
        await tags.delete(tag_name)
        request_url = str(route.calls[0].request.url)
        assert encoded in request_url
