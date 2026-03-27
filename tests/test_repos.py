from __future__ import annotations

import json

import httpx
import pytest
import respx

from gitforge.http import HttpClient
from gitforge.resources.repos import ReposResource
from gitforge.types import Repo, PaginatedResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_ID = "d361989f-a82e-4d64-aa30-25e6521e4f31"

REPO_JSON = {
    "id": REPO_ID,
    "name": "my-repo",
    "slug": "my-repo",
    "ownerSlug": "testuser",
    "description": "A test repository",
    "visibility": "public",
    "defaultBranch": "main",
    "lfsEnabled": False,
    "isArchived": False,
    "createdAt": "2026-03-01T00:00:00.000Z",
    "updatedAt": "2026-03-01T00:00:00.000Z",
    "starCount": 5,
    "openPrCount": 2,
    "openIssueCount": 0,
    "topics": ["python", "sdk"],
    "mergeCommitTemplate": None,
}


@pytest.fixture
def repos(http_client: HttpClient) -> ReposResource:
    return ReposResource(http_client)


def _repo_json(**overrides: object) -> dict:
    """Return a copy of REPO_JSON with optional overrides."""
    d = dict(REPO_JSON)
    d.update(overrides)
    return d


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestCreate:
    async def test_creates_repo_with_name_only(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=_repo_json(name="minimal"))
        )
        repo = await repos.create("minimal")
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body == {"name": "minimal"}
        assert isinstance(repo, Repo)
        assert repo.name == "minimal"

    async def test_creates_repo_with_all_options(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(
                200,
                json=_repo_json(
                    name="full-repo",
                    description="Full desc",
                    visibility="private",
                ),
            )
        )
        repo = await repos.create(
            "full-repo", description="Full desc", visibility="private"
        )
        body = json.loads(route.calls[0].request.content)
        assert body == {
            "name": "full-repo",
            "description": "Full desc",
            "visibility": "private",
        }
        assert repo.name == "full-repo"
        assert repo.description == "Full desc"
        assert repo.visibility == "private"

    async def test_returns_repo_dataclass_with_correct_fields(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=REPO_JSON)
        )
        repo = await repos.create("my-repo")
        assert repo.id == REPO_ID
        assert repo.name == "my-repo"
        assert repo.slug == "my-repo"
        assert repo.owner_slug == "testuser"
        assert repo.description == "A test repository"
        assert repo.visibility == "public"
        assert repo.default_branch == "main"
        assert repo.lfs_enabled is False
        assert repo.is_archived is False
        assert repo.created_at == "2026-03-01T00:00:00.000Z"
        assert repo.updated_at == "2026-03-01T00:00:00.000Z"
        assert repo.star_count == 5
        assert repo.open_pr_count == 2
        assert repo.open_issue_count == 0
        assert repo.topics == ["python", "sdk"]
        assert repo.merge_commit_template is None

    async def test_sends_post_to_repos(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=REPO_JSON)
        )
        await repos.create("test")
        assert route.calls[0].request.method == "POST"
        assert (
            str(route.calls[0].request.url) == "https://api.gitforge.dev/repos"
        )


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


class TestList:
    async def test_lists_repos_with_default_params(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = {
            "data": [REPO_JSON],
            "total": 1,
            "limit": 50,
            "offset": 0,
            "hasMore": False,
        }
        route = mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await repos.list()
        assert route.called
        request = route.calls[0].request
        assert request.method == "GET"
        # No limit/offset query params when defaults
        url_str = str(request.url)
        assert "limit=" not in url_str
        assert "offset=" not in url_str

    async def test_lists_repos_with_limit_and_offset(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = {
            "data": [REPO_JSON],
            "total": 100,
            "limit": 10,
            "offset": 20,
            "hasMore": True,
        }
        route = mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await repos.list(limit=10, offset=20)
        url_str = str(route.calls[0].request.url)
        assert "limit=10" in url_str
        assert "offset=20" in url_str
        assert result.limit == 10
        assert result.offset == 20

    async def test_returns_paginated_response_with_repo_objects(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        repo2 = _repo_json(id="r2", name="second-repo")
        paginated = {
            "data": [REPO_JSON, repo2],
            "total": 2,
            "limit": 50,
            "offset": 0,
            "hasMore": False,
        }
        mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await repos.list()
        assert isinstance(result, PaginatedResponse)
        assert len(result.data) == 2
        assert all(isinstance(r, Repo) for r in result.data)
        assert result.data[0].name == "my-repo"
        assert result.data[1].name == "second-repo"
        assert result.total == 2

    async def test_maps_has_more_correctly(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = {
            "data": [REPO_JSON],
            "total": 100,
            "limit": 1,
            "offset": 0,
            "hasMore": True,
        }
        mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await repos.list(limit=1)
        assert result.has_more is True

    async def test_handles_empty_list(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        paginated = {
            "data": [],
            "total": 0,
            "limit": 50,
            "offset": 0,
            "hasMore": False,
        }
        mock_router.get("https://api.gitforge.dev/repos").mock(
            return_value=httpx.Response(200, json=paginated)
        )
        result = await repos.list()
        assert result.data == []
        assert result.total == 0
        assert result.has_more is False


# ---------------------------------------------------------------------------
# get
# ---------------------------------------------------------------------------


class TestGet:
    async def test_gets_repo_by_id(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(return_value=httpx.Response(200, json=REPO_JSON))
        repo = await repos.get(REPO_ID)
        assert route.called
        assert route.calls[0].request.method == "GET"
        assert str(route.calls[0].request.url) == (
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        )
        assert isinstance(repo, Repo)
        assert repo.id == REPO_ID

    async def test_returns_repo_with_all_fields_mapped(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(return_value=httpx.Response(200, json=REPO_JSON))
        repo = await repos.get(REPO_ID)
        # Verify camelCase -> snake_case mapping
        assert repo.default_branch == "main"
        assert repo.lfs_enabled is False
        assert repo.is_archived is False
        assert repo.owner_slug == "testuser"
        assert repo.created_at == "2026-03-01T00:00:00.000Z"
        assert repo.updated_at == "2026-03-01T00:00:00.000Z"
        assert repo.star_count == 5
        assert repo.open_pr_count == 2
        assert repo.open_issue_count == 0
        assert repo.topics == ["python", "sdk"]


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------


class TestUpdate:
    async def test_updates_repo_name(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.patch(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(
            return_value=httpx.Response(
                200, json=_repo_json(name="renamed")
            )
        )
        repo = await repos.update(REPO_ID, name="renamed")
        body = json.loads(route.calls[0].request.content)
        assert body == {"name": "renamed"}
        assert repo.name == "renamed"

    async def test_updates_default_branch_sent_as_camel_case(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.patch(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(
            return_value=httpx.Response(
                200, json=_repo_json(defaultBranch="develop")
            )
        )
        repo = await repos.update(REPO_ID, default_branch="develop")
        body = json.loads(route.calls[0].request.content)
        assert body == {"defaultBranch": "develop"}
        assert repo.default_branch == "develop"

    async def test_updates_merge_commit_template(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        template = "Merge {{sourceBranch}} into {{targetBranch}}"
        route = mock_router.patch(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(
            return_value=httpx.Response(
                200, json=_repo_json(mergeCommitTemplate=template)
            )
        )
        repo = await repos.update(REPO_ID, merge_commit_template=template)
        body = json.loads(route.calls[0].request.content)
        assert body == {"mergeCommitTemplate": template}
        assert repo.merge_commit_template == template

    async def test_returns_updated_repo(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.patch(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(
            return_value=httpx.Response(
                200,
                json=_repo_json(
                    name="updated-name",
                    description="new desc",
                    defaultBranch="develop",
                ),
            )
        )
        repo = await repos.update(
            REPO_ID, name="updated-name", description="new desc", default_branch="develop"
        )
        assert isinstance(repo, Repo)
        assert repo.name == "updated-name"
        assert repo.description == "new desc"
        assert repo.default_branch == "develop"

    async def test_sends_patch_request(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.patch(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(
            return_value=httpx.Response(200, json=REPO_JSON)
        )
        await repos.update(REPO_ID, name="test")
        assert route.calls[0].request.method == "PATCH"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------


class TestDelete:
    async def test_deletes_repo_by_id(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(return_value=httpx.Response(204))
        result = await repos.delete(REPO_ID)
        assert route.called
        assert result is None

    async def test_sends_delete_to_correct_url(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        ).mock(return_value=httpx.Response(204))
        await repos.delete(REPO_ID)
        assert route.calls[0].request.method == "DELETE"
        assert str(route.calls[0].request.url) == (
            f"https://api.gitforge.dev/repos/{REPO_ID}"
        )


# ---------------------------------------------------------------------------
# create_note
# ---------------------------------------------------------------------------

SHA = "a" * 40
REF_SHA = "b" * 40
AUTHOR = {"name": "Jane", "email": "jane@example.com"}

NOTE_RESPONSE = {"sha": SHA, "refSha": REF_SHA, "success": True}


class TestCreateNote:
    async def test_sends_post_to_notes_endpoint(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        result = await repos.create_note(REPO_ID, SHA, "LGTM", AUTHOR)
        assert route.called
        assert route.calls[0].request.method == "POST"
        assert result["success"] is True

    async def test_sends_action_add_in_body(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        await repos.create_note(REPO_ID, SHA, "LGTM", AUTHOR)
        body = json.loads(route.calls[0].request.content)
        assert body["action"] == "add"
        assert body["sha"] == SHA
        assert body["note"] == "LGTM"
        assert body["author"] == AUTHOR

    async def test_includes_expected_ref_sha_when_provided(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        await repos.create_note(REPO_ID, SHA, "LGTM", AUTHOR, expected_ref_sha=REF_SHA)
        body = json.loads(route.calls[0].request.content)
        assert body["expectedRefSha"] == REF_SHA

    async def test_omits_expected_ref_sha_when_not_provided(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        await repos.create_note(REPO_ID, SHA, "LGTM", AUTHOR)
        body = json.loads(route.calls[0].request.content)
        assert "expectedRefSha" not in body


# ---------------------------------------------------------------------------
# append_note
# ---------------------------------------------------------------------------


class TestAppendNote:
    async def test_sends_post_with_action_append(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        await repos.append_note(REPO_ID, SHA, "More detail", AUTHOR)
        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body["action"] == "append"
        assert body["note"] == "More detail"

    async def test_returns_response_dict(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        result = await repos.append_note(REPO_ID, SHA, "Extra", AUTHOR)
        assert result["sha"] == SHA


# ---------------------------------------------------------------------------
# get_note
# ---------------------------------------------------------------------------


class TestGetNote:
    async def test_sends_get_to_note_url(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        note_data = {"sha": SHA, "note": "LGTM", "refSha": REF_SHA}
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes/{SHA}"
        ).mock(return_value=httpx.Response(200, json=note_data))
        result = await repos.get_note(REPO_ID, SHA)
        assert route.called
        assert route.calls[0].request.method == "GET"
        assert result["note"] == "LGTM"
        assert result["sha"] == SHA

    async def test_returns_note_data(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        note_data = {"sha": SHA, "note": "Review done", "refSha": REF_SHA}
        mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes/{SHA}"
        ).mock(return_value=httpx.Response(200, json=note_data))
        result = await repos.get_note(REPO_ID, SHA)
        assert result["note"] == "Review done"


# ---------------------------------------------------------------------------
# delete_note
# ---------------------------------------------------------------------------


class TestDeleteNote:
    async def test_sends_delete_with_author_body(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes/{SHA}"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        await repos.delete_note(REPO_ID, SHA, author=AUTHOR)
        assert route.called
        assert route.calls[0].request.method == "DELETE"
        body = json.loads(route.calls[0].request.content)
        assert body["author"] == AUTHOR

    async def test_includes_expected_ref_sha_when_provided(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes/{SHA}"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        await repos.delete_note(REPO_ID, SHA, author=AUTHOR, expected_ref_sha=REF_SHA)
        body = json.loads(route.calls[0].request.content)
        assert body["expectedRefSha"] == REF_SHA

    async def test_sends_delete_with_no_body_when_no_params(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(
            f"https://api.gitforge.dev/repos/{REPO_ID}/notes/{SHA}"
        ).mock(return_value=httpx.Response(200, json=NOTE_RESPONSE))
        await repos.delete_note(REPO_ID, SHA)
        assert route.called
        assert route.calls[0].request.method == "DELETE"


# ---------------------------------------------------------------------------
# restore_commit
# ---------------------------------------------------------------------------

COMMIT_SHA = "c" * 40


class TestRestoreCommit:
    async def test_sends_post_to_restore_commit_endpoint(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        response_data = {"commitSha": COMMIT_SHA, "treeSha": "d" * 40, "success": True}
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/restore-commit"
        ).mock(return_value=httpx.Response(200, json=response_data))
        result = await repos.restore_commit(REPO_ID, "main", COMMIT_SHA, AUTHOR)
        assert route.called
        assert route.calls[0].request.method == "POST"
        assert result["success"] is True

    async def test_sends_required_fields_in_body(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        response_data = {"commitSha": COMMIT_SHA, "treeSha": "d" * 40, "success": True}
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/restore-commit"
        ).mock(return_value=httpx.Response(200, json=response_data))
        await repos.restore_commit(REPO_ID, "main", COMMIT_SHA, AUTHOR)
        body = json.loads(route.calls[0].request.content)
        assert body["targetBranch"] == "main"
        assert body["targetCommitSha"] == COMMIT_SHA
        assert body["author"] == AUTHOR

    async def test_includes_optional_fields_when_provided(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        response_data = {"commitSha": COMMIT_SHA, "treeSha": "d" * 40, "success": True}
        committer = {"name": "Bot", "email": "bot@example.com"}
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/restore-commit"
        ).mock(return_value=httpx.Response(200, json=response_data))
        await repos.restore_commit(
            REPO_ID,
            "main",
            COMMIT_SHA,
            AUTHOR,
            committer=committer,
            commit_message="Restore to stable",
            expected_head_sha=SHA,
        )
        body = json.loads(route.calls[0].request.content)
        assert body["committer"] == committer
        assert body["commitMessage"] == "Restore to stable"
        assert body["expectedHeadSha"] == SHA

    async def test_omits_optional_fields_when_not_provided(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        response_data = {"commitSha": COMMIT_SHA, "treeSha": "d" * 40, "success": True}
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/restore-commit"
        ).mock(return_value=httpx.Response(200, json=response_data))
        await repos.restore_commit(REPO_ID, "main", COMMIT_SHA, AUTHOR)
        body = json.loads(route.calls[0].request.content)
        assert "committer" not in body
        assert "commitMessage" not in body
        assert "expectedHeadSha" not in body


# ---------------------------------------------------------------------------
# list_files_with_metadata
# ---------------------------------------------------------------------------

FILES_METADATA_RESPONSE = {
    "files": [
        {"path": "README.md", "sha": SHA, "size": 100, "type": "blob"}
    ],
    "commits": {SHA: {"sha": SHA, "message": "Initial commit"}},
    "ref": "main",
}


class TestListFilesWithMetadata:
    async def test_sends_get_to_metadata_endpoint(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/files/metadata"
        ).mock(return_value=httpx.Response(200, json=FILES_METADATA_RESPONSE))
        result = await repos.list_files_with_metadata(REPO_ID, ref="main")
        assert route.called
        assert route.calls[0].request.method == "GET"
        assert result["ref"] == "main"

    async def test_passes_ref_as_query_param(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/files/metadata"
        ).mock(return_value=httpx.Response(200, json=FILES_METADATA_RESPONSE))
        await repos.list_files_with_metadata(REPO_ID, ref="develop")
        url_str = str(route.calls[0].request.url)
        assert "ref=develop" in url_str

    async def test_passes_ephemeral_as_query_param(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/files/metadata"
        ).mock(return_value=httpx.Response(200, json=FILES_METADATA_RESPONSE))
        await repos.list_files_with_metadata(REPO_ID, ephemeral=True)
        url_str = str(route.calls[0].request.url)
        assert "ephemeral=true" in url_str

    async def test_omits_optional_params_when_not_provided(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/files/metadata"
        ).mock(return_value=httpx.Response(200, json=FILES_METADATA_RESPONSE))
        await repos.list_files_with_metadata(REPO_ID)
        url_str = str(route.calls[0].request.url)
        assert "ref=" not in url_str
        assert "ephemeral=" not in url_str


# ---------------------------------------------------------------------------
# pull_upstream
# ---------------------------------------------------------------------------

PULL_UPSTREAM_RESPONSE = {
    "status": "fast_forward",
    "success": True,
    "oldSha": SHA,
    "newSha": REF_SHA,
    "branch": "main",
}


class TestPullUpstream:
    async def test_sends_post_to_pull_upstream_endpoint(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/pull-upstream"
        ).mock(return_value=httpx.Response(200, json=PULL_UPSTREAM_RESPONSE))
        result = await repos.pull_upstream(REPO_ID, branch="main")
        assert route.called
        assert route.calls[0].request.method == "POST"
        assert result["status"] == "fast_forward"

    async def test_includes_branch_in_body_when_provided(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/pull-upstream"
        ).mock(return_value=httpx.Response(200, json=PULL_UPSTREAM_RESPONSE))
        await repos.pull_upstream(REPO_ID, branch="feature")
        body = json.loads(route.calls[0].request.content)
        assert body["branch"] == "feature"

    async def test_sends_empty_body_when_no_branch(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.post(
            f"https://api.gitforge.dev/repos/{REPO_ID}/pull-upstream"
        ).mock(return_value=httpx.Response(200, json=PULL_UPSTREAM_RESPONSE))
        await repos.pull_upstream(REPO_ID)
        body = json.loads(route.calls[0].request.content) if route.calls[0].request.content else {}
        assert "branch" not in body


# ---------------------------------------------------------------------------
# detach_upstream
# ---------------------------------------------------------------------------


class TestDetachUpstream:
    async def test_sends_delete_to_base_endpoint(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(
            f"https://api.gitforge.dev/repos/{REPO_ID}/base"
        ).mock(return_value=httpx.Response(200, json={"message": "repository detached"}))
        result = await repos.detach_upstream(REPO_ID)
        assert route.called
        assert route.calls[0].request.method == "DELETE"
        assert result["message"] == "repository detached"

    async def test_sends_delete_to_correct_url(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.delete(
            f"https://api.gitforge.dev/repos/{REPO_ID}/base"
        ).mock(return_value=httpx.Response(200, json={"message": "ok"}))
        await repos.detach_upstream(REPO_ID)
        assert str(route.calls[0].request.url) == (
            f"https://api.gitforge.dev/repos/{REPO_ID}/base"
        )


# ---------------------------------------------------------------------------
# get_raw_file
# ---------------------------------------------------------------------------

RAW_CONTENT = b"# Hello World\n"


class TestGetRawFile:
    async def test_sends_get_to_raw_endpoint(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/raw/main"
        ).mock(return_value=httpx.Response(200, content=RAW_CONTENT))
        result = await repos.get_raw_file(REPO_ID, "main", "README.md")
        assert route.called
        assert route.calls[0].request.method == "GET"
        assert isinstance(result, bytes)
        assert result == RAW_CONTENT

    async def test_passes_path_as_query_param(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/raw/main"
        ).mock(return_value=httpx.Response(200, content=RAW_CONTENT))
        await repos.get_raw_file(REPO_ID, "main", "src/main.py")
        url_str = str(route.calls[0].request.url)
        assert "path=src%2Fmain.py" in url_str or "path=src/main.py" in url_str

    async def test_passes_download_param_when_true(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/raw/main"
        ).mock(return_value=httpx.Response(200, content=RAW_CONTENT))
        await repos.get_raw_file(REPO_ID, "main", "README.md", download=True)
        url_str = str(route.calls[0].request.url)
        assert "download=true" in url_str

    async def test_omits_download_param_by_default(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        route = mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/raw/main"
        ).mock(return_value=httpx.Response(200, content=RAW_CONTENT))
        await repos.get_raw_file(REPO_ID, "main", "README.md")
        url_str = str(route.calls[0].request.url)
        assert "download=" not in url_str

    async def test_returns_raw_bytes(
        self, repos: ReposResource, mock_router: respx.MockRouter
    ) -> None:
        binary_content = bytes(range(256))
        mock_router.get(
            f"https://api.gitforge.dev/repos/{REPO_ID}/raw/main"
        ).mock(return_value=httpx.Response(200, content=binary_content))
        result = await repos.get_raw_file(REPO_ID, "main", "binary.bin")
        assert result == binary_content
