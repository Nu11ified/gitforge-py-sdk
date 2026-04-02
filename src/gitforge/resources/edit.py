from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient


class EditResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def apply(
        self,
        repo_id: str,
        edits: list[dict[str, Any]],
        ref: Optional[str] = None,
        commit: bool = False,
        validate: bool = False,
        message: Optional[str] = None,
        author: Optional[dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Apply structured edits to repository files.

        Each edit in the list should be a dict with a ``type`` key
        (``text-patch``, ``metadata``, or ``binary-patch``) and the
        corresponding fields for that edit type.
        """
        body: dict[str, Any] = {"edits": edits}
        if ref is not None:
            body["ref"] = ref
        if commit:
            body["commit"] = True
        if validate:
            body["validate"] = True
        if message is not None:
            body["message"] = message
        if author is not None:
            body["author"] = author
        if session_id is not None:
            body["sessionId"] = session_id
        return await self._http.post(f"/edit/{repo_id}", body)

    async def context(
        self,
        repo_id: str,
        paths: list[str],
        ref: Optional[str] = None,
        surrounding_lines: Optional[int] = None,
    ) -> dict[str, Any]:
        """Read file context for agents.

        Returns file contents (optionally truncated) for the requested paths.
        """
        query: dict[str, str] = {
            "paths": ",".join(paths),
        }
        if ref is not None:
            query["ref"] = ref
        if surrounding_lines is not None:
            query["surroundingLines"] = str(surrounding_lines)
        return await self._http.get(f"/edit/{repo_id}/context", query)

    async def create_session(
        self,
        repo_id: str,
        branch: str,
        source_ref: str = "main",
        description: Optional[str] = None,
        ttl_hours: Optional[int] = None,
    ) -> dict[str, Any]:
        """Create a multi-step edit session with its own branch."""
        body: dict[str, Any] = {
            "repoId": repo_id,
            "branch": branch,
            "sourceRef": source_ref,
        }
        if description is not None:
            body["description"] = description
        if ttl_hours is not None:
            body["ttlHours"] = ttl_hours
        return await self._http.post("/edit/sessions", body)

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get the current status of an edit session."""
        return await self._http.get(f"/edit/sessions/{session_id}")

    async def submit_session(
        self,
        session_id: str,
        title: str,
        target_branch: str,
        body: Optional[str] = None,
    ) -> dict[str, Any]:
        """Submit an edit session as a pull request."""
        payload: dict[str, Any] = {
            "title": title,
            "targetBranch": target_branch,
        }
        if body is not None:
            payload["body"] = body
        return await self._http.post(
            f"/edit/sessions/{session_id}/submit", payload,
        )
