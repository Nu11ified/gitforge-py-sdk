from __future__ import annotations

import json

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.mirrors import MirrorsResource
from gitforge.types import MirrorConfig


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

BASE_URL = "https://api.gitforge.dev"
REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"
MIRROR_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
MIRRORS_URL = f"{BASE_URL}/repos/{REPO_ID}/mirrors"

MIRROR_JSON = {
    "id": MIRROR_ID,
    "sourceUrl": "https://github.com/example/repo.git",
    "interval": 3600,
    "enabled": True,
    "direction": "pull",
    "provider": "github",
    "createdAt": "2026-03-20T10:00:00.000Z",
    "lastSyncAt": None,
    "lastError": None,
    "credentialId": None,
}


def _mirror_json(**overrides: object) -> dict:
    d = dict(MIRROR_JSON)
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mirrors(http_client: HttpClient) -> MirrorsResource:
    return MirrorsResource(http_client, REPO_ID)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    async def test_sends_get_to_mirrors_url(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(MIRRORS_URL).mock(
            return_value=httpx.Response(200, json=[_mirror_json()])
        )
        await mirrors.list()
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"

    async def test_returns_list_of_mirror_config(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        m1 = _mirror_json(id="mirror-1")
        m2 = _mirror_json(id="mirror-2", direction="push")
        mock_router.get(MIRRORS_URL).mock(
            return_value=httpx.Response(200, json=[m1, m2])
        )
        result = await mirrors.list()
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(m, MirrorConfig) for m in result)
        assert result[0].id == "mirror-1"
        assert result[1].id == "mirror-2"
        assert result[1].direction == "push"

    async def test_returns_empty_list(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(MIRRORS_URL).mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await mirrors.list()
        assert result == []

    async def test_deserialises_all_fields(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(MIRRORS_URL).mock(
            return_value=httpx.Response(
                200,
                json=[
                    _mirror_json(
                        lastSyncAt="2026-03-25T12:00:00.000Z",
                        lastError="connection timeout",
                        credentialId="cred-abc",
                    )
                ],
            )
        )
        result = await mirrors.list()
        m = result[0]
        assert m.id == MIRROR_ID
        assert m.source_url == "https://github.com/example/repo.git"
        assert m.interval == 3600
        assert m.enabled is True
        assert m.direction == "pull"
        assert m.provider == "github"
        assert m.created_at == "2026-03-20T10:00:00.000Z"
        assert m.last_sync_at == "2026-03-25T12:00:00.000Z"
        assert m.last_error == "connection timeout"
        assert m.credential_id == "cred-abc"


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_sends_post_with_required_fields(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(MIRRORS_URL).mock(
            return_value=httpx.Response(201, json=_mirror_json())
        )
        await mirrors.create(source_url="https://github.com/example/repo.git")
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {
            "sourceUrl": "https://github.com/example/repo.git",
            "direction": "pull",
        }

    async def test_sends_post_with_all_options(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(MIRRORS_URL).mock(
            return_value=httpx.Response(
                201,
                json=_mirror_json(
                    interval=1800,
                    direction="push",
                    credentialId="cred-uuid-123",
                ),
            )
        )
        await mirrors.create(
            source_url="https://github.com/example/repo.git",
            direction="push",
            interval=1800,
            credential_id="cred-uuid-123",
        )
        body = json.loads(route.calls[0].request.content)
        assert body == {
            "sourceUrl": "https://github.com/example/repo.git",
            "direction": "push",
            "interval": 1800,
            "credentialId": "cred-uuid-123",
        }

    async def test_returns_mirror_config(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post(MIRRORS_URL).mock(
            return_value=httpx.Response(
                201,
                json=_mirror_json(id="mirror-new", direction="push", interval=1800),
            )
        )
        result = await mirrors.create(
            source_url="https://github.com/example/repo.git",
            direction="push",
            interval=1800,
        )
        assert isinstance(result, MirrorConfig)
        assert result.id == "mirror-new"
        assert result.direction == "push"
        assert result.interval == 1800
        assert result.created_at == "2026-03-20T10:00:00.000Z"

    async def test_omits_none_optional_fields(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(MIRRORS_URL).mock(
            return_value=httpx.Response(201, json=_mirror_json())
        )
        await mirrors.create(source_url="https://github.com/example/repo.git")
        body = json.loads(route.calls[0].request.content)
        assert "interval" not in body
        assert "credentialId" not in body


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    async def test_sends_patch_with_interval(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{MIRRORS_URL}/{MIRROR_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(200, json=_mirror_json(interval=7200))
        )
        result = await mirrors.update(MIRROR_ID, interval=7200)
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {"interval": 7200}
        assert result.interval == 7200

    async def test_sends_patch_with_enabled(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{MIRRORS_URL}/{MIRROR_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(200, json=_mirror_json(enabled=False))
        )
        result = await mirrors.update(MIRROR_ID, enabled=False)
        body = json.loads(route.calls[0].request.content)
        assert body == {"enabled": False}
        assert result.enabled is False

    async def test_sends_patch_with_credential_id(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{MIRRORS_URL}/{MIRROR_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(
                200, json=_mirror_json(credentialId="cred-456")
            )
        )
        result = await mirrors.update(MIRROR_ID, credential_id="cred-456")
        body = json.loads(route.calls[0].request.content)
        assert body == {"credentialId": "cred-456"}
        assert result.credential_id == "cred-456"

    async def test_sends_patch_with_multiple_fields(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{MIRRORS_URL}/{MIRROR_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(
                200,
                json=_mirror_json(
                    interval=1800, enabled=False, credentialId="cred-789"
                ),
            )
        )
        result = await mirrors.update(
            MIRROR_ID, interval=1800, enabled=False, credential_id="cred-789"
        )
        body = json.loads(route.calls[0].request.content)
        assert body == {
            "interval": 1800,
            "enabled": False,
            "credentialId": "cred-789",
        }
        assert result.interval == 1800
        assert result.enabled is False
        assert result.credential_id == "cred-789"

    async def test_returns_mirror_config(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{MIRRORS_URL}/{MIRROR_ID}"
        mock_router.patch(url).mock(
            return_value=httpx.Response(200, json=_mirror_json(enabled=False))
        )
        result = await mirrors.update(MIRROR_ID, enabled=False)
        assert isinstance(result, MirrorConfig)
        assert result.id == MIRROR_ID

    async def test_omits_none_fields(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{MIRRORS_URL}/{MIRROR_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(200, json=_mirror_json())
        )
        await mirrors.update(MIRROR_ID, interval=3600)
        body = json.loads(route.calls[0].request.content)
        assert "enabled" not in body
        assert "credentialId" not in body


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_sends_delete_request(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{MIRRORS_URL}/{MIRROR_ID}"
        route = mock_router.delete(url).mock(
            return_value=httpx.Response(204)
        )
        result = await mirrors.delete(MIRROR_ID)
        assert route.called
        assert result is None

    async def test_sends_delete_to_correct_url(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        other_id = "mirror-9999-delete-me"
        url = f"{MIRRORS_URL}/{other_id}"
        route = mock_router.delete(url).mock(
            return_value=httpx.Response(204)
        )
        await mirrors.delete(other_id)
        request = route.calls[0].request
        assert str(request.url) == url
        assert request.method == "DELETE"


# ---------------------------------------------------------------------------
# sync
# ---------------------------------------------------------------------------


class TestSync:
    async def test_sends_post_to_sync_url(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{MIRRORS_URL}/{MIRROR_ID}/sync"
        route = mock_router.post(url).mock(
            return_value=httpx.Response(200, json={"status": "started"})
        )
        result = await mirrors.sync(MIRROR_ID)
        assert route.called
        request = route.calls[0].request
        assert request.method == "POST"
        assert isinstance(result, dict)
        assert result["status"] == "started"

    async def test_sends_post_to_correct_mirror_id(
        self, mirrors: MirrorsResource, mock_router: respx.MockRouter
    ) -> None:
        other_id = "mirror-sync-specific"
        url = f"{MIRRORS_URL}/{other_id}/sync"
        route = mock_router.post(url).mock(
            return_value=httpx.Response(200, json={"status": "queued"})
        )
        result = await mirrors.sync(other_id)
        request = route.calls[0].request
        assert str(request.url) == url
        assert isinstance(result, dict)
