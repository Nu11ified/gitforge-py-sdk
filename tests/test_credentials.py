from __future__ import annotations

import json

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.credentials import CredentialsResource
from gitforge.types import GitCredential, PaginatedResponse


# ---------------------------------------------------------------------------
# Constants & helpers
# ---------------------------------------------------------------------------

BASE_URL = "https://api.gitforge.dev"
CRED_ID = "cred-0001-aaaa-bbbb-cccc"
CREDENTIALS_URL = f"{BASE_URL}/git-credentials"

CREDENTIAL_JSON = {
    "id": CRED_ID,
    "provider": "github",
    "username": None,
    "label": None,
    "createdAt": "2026-03-26T12:00:00.000Z",
}


def _cred_json(**overrides: object) -> dict:
    d = dict(CREDENTIAL_JSON)
    d.update(overrides)
    return d


def _paginated(*items: dict) -> dict:
    return {
        "data": list(items),
        "total": len(items),
        "limit": 20,
        "offset": 0,
        "hasMore": False,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def credentials(http_client: HttpClient) -> CredentialsResource:
    return CredentialsResource(http_client)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_sends_post_with_required_fields(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(CREDENTIALS_URL).mock(
            return_value=httpx.Response(201, json=_cred_json())
        )
        await credentials.create(provider="github", token="ghp_abc123")
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {"provider": "github", "token": "ghp_abc123"}

    async def test_sends_post_with_all_options(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(CREDENTIALS_URL).mock(
            return_value=httpx.Response(
                201,
                json=_cred_json(
                    provider="gitlab",
                    username="myuser",
                    label="CI mirror token",
                ),
            )
        )
        await credentials.create(
            provider="gitlab",
            token="glpat_xyz789",
            username="myuser",
            label="CI mirror token",
        )
        body = json.loads(route.calls[0].request.content)
        assert body == {
            "provider": "gitlab",
            "token": "glpat_xyz789",
            "username": "myuser",
            "label": "CI mirror token",
        }

    async def test_returns_git_credential(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post(CREDENTIALS_URL).mock(
            return_value=httpx.Response(
                201,
                json=_cred_json(
                    id="cred-new",
                    provider="github",
                    username="octocat",
                    label="My token",
                ),
            )
        )
        result = await credentials.create(provider="github", token="ghp_secret")
        assert isinstance(result, GitCredential)
        assert result.id == "cred-new"
        assert result.provider == "github"
        assert result.username == "octocat"
        assert result.label == "My token"
        assert result.created_at == "2026-03-26T12:00:00.000Z"

    async def test_omits_none_optional_fields(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(CREDENTIALS_URL).mock(
            return_value=httpx.Response(201, json=_cred_json())
        )
        await credentials.create(provider="github", token="ghp_abc")
        body = json.loads(route.calls[0].request.content)
        assert "username" not in body
        assert "label" not in body


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    async def test_sends_get_with_default_params(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(CREDENTIALS_URL).mock(
            return_value=httpx.Response(200, json=_paginated())
        )
        await credentials.list()
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"

    async def test_sends_get_with_limit_and_offset(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(CREDENTIALS_URL).mock(
            return_value=httpx.Response(200, json=_paginated())
        )
        await credentials.list(limit=10, offset=5)
        url = str(route.calls[0].request.url)
        assert "limit=10" in url
        assert "offset=5" in url

    async def test_returns_paginated_response(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        cred1 = _cred_json(id="cred-1", provider="github")
        cred2 = _cred_json(id="cred-2", provider="gitlab", label="backup")
        mock_router.get(CREDENTIALS_URL).mock(
            return_value=httpx.Response(200, json=_paginated(cred1, cred2))
        )
        result = await credentials.list()
        assert isinstance(result, PaginatedResponse)
        assert result.total == 2
        assert result.limit == 20
        assert result.offset == 0
        assert result.has_more is False
        assert len(result.data) == 2
        assert all(isinstance(c, GitCredential) for c in result.data)
        assert result.data[0].id == "cred-1"
        assert result.data[1].label == "backup"

    async def test_returns_empty_paginated_response(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(CREDENTIALS_URL).mock(
            return_value=httpx.Response(200, json=_paginated())
        )
        result = await credentials.list()
        assert result.total == 0
        assert result.data == []


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    async def test_sends_patch_with_token(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{CREDENTIALS_URL}/{CRED_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(200, json=_cred_json())
        )
        await credentials.update(CRED_ID, token="ghp_new_token_456")
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {"token": "ghp_new_token_456"}

    async def test_sends_patch_with_label(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{CREDENTIALS_URL}/{CRED_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(200, json=_cred_json(label="Updated label"))
        )
        result = await credentials.update(CRED_ID, label="Updated label")
        body = json.loads(route.calls[0].request.content)
        assert body == {"label": "Updated label"}
        assert result.label == "Updated label"

    async def test_sends_patch_with_username(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{CREDENTIALS_URL}/{CRED_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(200, json=_cred_json(username="newuser"))
        )
        result = await credentials.update(CRED_ID, username="newuser")
        body = json.loads(route.calls[0].request.content)
        assert body == {"username": "newuser"}
        assert result.username == "newuser"

    async def test_returns_git_credential(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{CREDENTIALS_URL}/{CRED_ID}"
        mock_router.patch(url).mock(
            return_value=httpx.Response(
                200,
                json=_cred_json(label="Refreshed"),
            )
        )
        result = await credentials.update(CRED_ID, label="Refreshed")
        assert isinstance(result, GitCredential)
        assert result.id == CRED_ID
        assert result.label == "Refreshed"

    async def test_omits_none_fields(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{CREDENTIALS_URL}/{CRED_ID}"
        route = mock_router.patch(url).mock(
            return_value=httpx.Response(200, json=_cred_json())
        )
        await credentials.update(CRED_ID, token="ghp_only")
        body = json.loads(route.calls[0].request.content)
        assert "username" not in body
        assert "label" not in body


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_sends_delete_request(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        url = f"{CREDENTIALS_URL}/{CRED_ID}"
        route = mock_router.delete(url).mock(
            return_value=httpx.Response(204)
        )
        result = await credentials.delete(CRED_ID)
        assert route.called
        assert result is None

    async def test_sends_delete_to_correct_url(
        self, credentials: CredentialsResource, mock_router: respx.MockRouter
    ) -> None:
        other_id = "cred-9999-delete-me"
        url = f"{CREDENTIALS_URL}/{other_id}"
        route = mock_router.delete(url).mock(
            return_value=httpx.Response(204)
        )
        await credentials.delete(other_id)
        request = route.calls[0].request
        assert str(request.url) == url
        assert request.method == "DELETE"
