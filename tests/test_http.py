from __future__ import annotations

import httpx
import pytest
import respx

from gitforge.errors import GitForgeError, RefUpdateError
from gitforge.http import HttpClient


# ---------------------------------------------------------------------------
# Authentication tests
# ---------------------------------------------------------------------------


class TestAuthentication:
    async def test_sends_bearer_token_on_get(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        await http_client.get("/repos")
        assert route.called
        request = route.calls[0].request
        assert request.headers["authorization"] == "Bearer gf_test_token_abc123"

    async def test_sends_bearer_token_on_post(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json={"id": "1"})
        )
        await http_client.post("/repos", {"name": "test"})
        request = route.calls[0].request
        assert request.headers["authorization"] == "Bearer gf_test_token_abc123"

    async def test_sends_bearer_token_on_patch(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.patch("https://api.gitforge.dev/repos/1").mock(
            return_value=httpx.Response(200, json={"id": "1"})
        )
        await http_client.patch("/repos/1", {"name": "updated"})
        request = route.calls[0].request
        assert request.headers["authorization"] == "Bearer gf_test_token_abc123"

    async def test_sends_bearer_token_on_delete(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete("https://api.gitforge.dev/repos/1").mock(
            return_value=httpx.Response(204)
        )
        await http_client.delete("/repos/1")
        request = route.calls[0].request
        assert request.headers["authorization"] == "Bearer gf_test_token_abc123"


# ---------------------------------------------------------------------------
# URL construction tests
# ---------------------------------------------------------------------------


class TestUrlConstruction:
    async def test_builds_full_url_from_base_url_and_path(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=[])
        )
        await http_client.get("/repos")
        request = route.calls[0].request
        assert str(request.url).rstrip("?") == "https://api.gitforge.dev/repos"

    async def test_strips_trailing_slashes_from_base_url(
        self, token: str, mock_router: respx.MockRouter
    ) -> None:
        client = HttpClient(
            base_url="https://api.gitforge.dev///",
            token=token,
            client=httpx.AsyncClient(),
        )
        route = mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=[])
        )
        await client.get("/repos")
        request = route.calls[0].request
        # After stripping trailing slashes, URL should be clean
        assert str(request.url).rstrip("?") == "https://api.gitforge.dev/repos"

    async def test_appends_query_params_to_get(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        await http_client.get("/repos", {"limit": "10", "offset": "20"})
        request = route.calls[0].request
        url = str(request.url)
        assert "limit=10" in url
        assert "offset=20" in url

    async def test_does_not_append_query_string_when_empty(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=[])
        )
        await http_client.get("/repos", {})
        request = route.calls[0].request
        # With empty params dict, no meaningful query string
        url_str = str(request.url)
        # httpx may append a trailing '?' with empty params, but no key=value pairs
        if "?" in url_str:
            query_part = url_str.split("?", 1)[1]
            assert query_part == ""


# ---------------------------------------------------------------------------
# POST tests
# ---------------------------------------------------------------------------


class TestPost:
    async def test_sends_json_body_with_content_type(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json={"id": "new-repo"})
        )
        await http_client.post("/repos", {"name": "my-repo", "visibility": "private"})
        request = route.calls[0].request
        assert request.headers["content-type"] == "application/json"
        import json

        body = json.loads(request.content)
        assert body == {"name": "my-repo", "visibility": "private"}

    async def test_sends_no_body_when_none_provided(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post("https://api.gitforge.dev/repos/1/sync").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        await http_client.post("/repos/1/sync")
        request = route.calls[0].request
        # No JSON body should be sent
        assert request.content == b""


# ---------------------------------------------------------------------------
# PATCH tests
# ---------------------------------------------------------------------------


class TestPatch:
    async def test_sends_json_body_with_content_type(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.patch("https://api.gitforge.dev/repos/1").mock(
            return_value=httpx.Response(200, json={"id": "1", "name": "updated"})
        )
        await http_client.patch("/repos/1", {"name": "updated"})
        request = route.calls[0].request
        assert request.headers["content-type"] == "application/json"
        import json

        body = json.loads(request.content)
        assert body == {"name": "updated"}


# ---------------------------------------------------------------------------
# DELETE tests
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_returns_none_on_204(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.delete("https://api.gitforge.dev/repos/1").mock(
            return_value=httpx.Response(204)
        )
        result = await http_client.delete("/repos/1")
        assert result is None

    async def test_supports_query_parameters(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete("https://api.gitforge.dev/refs/heads/feature").mock(
            return_value=httpx.Response(204)
        )
        await http_client.delete("/refs/heads/feature", {"force": "true"})
        request = route.calls[0].request
        assert "force=true" in str(request.url)


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    async def test_maps_non_ok_to_gitforge_error(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get("https://api.gitforge.dev/repos/secret").mock(
            return_value=httpx.Response(
                403, json={"code": "forbidden", "message": "You do not have access"}
            )
        )
        with pytest.raises(GitForgeError) as exc_info:
            await http_client.get("/repos/secret")
        err = exc_info.value
        assert err.status == 403
        assert err.code == "forbidden"
        assert err.message == "You do not have access"

    async def test_handles_404_not_found(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get("https://api.gitforge.dev/repos/nonexistent").mock(
            return_value=httpx.Response(
                404, json={"code": "not_found", "message": "Repository not found"}
            )
        )
        with pytest.raises(GitForgeError) as exc_info:
            await http_client.get("/repos/nonexistent")
        err = exc_info.value
        assert err.status == 404
        assert err.code == "not_found"
        assert err.message == "Repository not found"

    async def test_handles_409_conflict(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post("https://api.gitforge.dev/repos/1/commits").mock(
            return_value=httpx.Response(
                409, json={"code": "branch_moved", "message": "Branch was updated"}
            )
        )
        with pytest.raises(GitForgeError) as exc_info:
            await http_client.post("/repos/1/commits", {"branch": "main"})
        err = exc_info.value
        assert err.status == 409
        assert err.code == "branch_moved"

    async def test_throws_ref_update_error_on_409_with_current_sha(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post("https://api.gitforge.dev/repos/1/commits").mock(
            return_value=httpx.Response(
                409,
                json={
                    "error": "branch_moved",
                    "currentSha": "abc123def456",
                },
            )
        )
        with pytest.raises(RefUpdateError) as exc_info:
            await http_client.post("/repos/1/commits", {"branch": "main"})
        err = exc_info.value
        assert isinstance(err, GitForgeError)
        assert err.status == 409
        assert err.code == "branch_moved"
        assert err.current_sha == "abc123def456"

    async def test_handles_non_json_error_body(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(
                502,
                content=b"<html>Bad Gateway</html>",
                headers={"content-type": "text/html"},
            )
        )
        with pytest.raises(GitForgeError) as exc_info:
            await http_client.get("/repos")
        err = exc_info.value
        assert err.status == 502
        assert err.code == "unknown"
        assert err.message == "HTTP 502"

    async def test_handles_500_internal_server_error(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(
                500, json={"code": "internal", "message": "Something went wrong"}
            )
        )
        with pytest.raises(GitForgeError) as exc_info:
            await http_client.get("/repos")
        err = exc_info.value
        assert err.status == 500
        assert err.code == "internal"
        assert err.message == "Something went wrong"

    async def test_uses_fallback_code_and_message_when_body_lacks_them(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(502, json={})
        )
        with pytest.raises(GitForgeError) as exc_info:
            await http_client.get("/repos")
        err = exc_info.value
        assert err.status == 502
        assert err.code == "unknown"
        assert err.message == "HTTP 502"

    async def test_reads_both_code_and_error_keys(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        """Prefers 'code' key, falls back to 'error' key."""
        # Test with 'code' key
        mock_router.get("https://api.gitforge.dev/repos/a").mock(
            return_value=httpx.Response(
                400, json={"code": "validation_error", "message": "Bad input"}
            )
        )
        with pytest.raises(GitForgeError) as exc_info:
            await http_client.get("/repos/a")
        assert exc_info.value.code == "validation_error"

        # Test with 'error' key (no 'code')
        mock_router.get("https://api.gitforge.dev/repos/b").mock(
            return_value=httpx.Response(
                400, json={"error": "invalid_request", "message": "Missing field"}
            )
        )
        with pytest.raises(GitForgeError) as exc_info:
            await http_client.get("/repos/b")
        assert exc_info.value.code == "invalid_request"


# ---------------------------------------------------------------------------
# Response handling tests
# ---------------------------------------------------------------------------


class TestResponseHandling:
    async def test_handles_204_no_content_returns_none(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.delete("https://api.gitforge.dev/repos/1").mock(
            return_value=httpx.Response(204)
        )
        result = await http_client.delete("/repos/1")
        assert result is None

    async def test_returns_parsed_json_on_success(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        payload = {"id": "repo-1", "name": "test-repo"}
        mock_router.get("https://api.gitforge.dev/repos/repo-1").mock(
            return_value=httpx.Response(200, json=payload)
        )
        result = await http_client.get("/repos/repo-1")
        assert result == payload


# ---------------------------------------------------------------------------
# Sequential request tests
# ---------------------------------------------------------------------------


class TestSequentialRequests:
    async def test_multiple_sequential_requests(
        self, http_client: HttpClient, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get("https://api.gitforge.dev/repos/1").mock(
            return_value=httpx.Response(200, json={"id": "1"})
        )
        mock_router.post("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json={"id": "2"})
        )
        mock_router.patch("https://api.gitforge.dev/repos/1").mock(
            return_value=httpx.Response(200, json={"id": "3"})
        )

        r1 = await http_client.get("/repos/1")
        r2 = await http_client.post("/repos", {"name": "new"})
        r3 = await http_client.patch("/repos/1", {"name": "updated"})

        assert r1 == {"id": "1"}
        assert r2 == {"id": "2"}
        assert r3 == {"id": "3"}
