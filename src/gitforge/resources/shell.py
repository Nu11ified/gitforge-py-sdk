from __future__ import annotations

from typing import Any, Optional

from ..http import HttpClient
from ..types import ShellExecResult, ShellMultiExecResult, ShellDestroyResult, ShellMount
from .._util import _from_dict


class RepoShellResource:
    def __init__(self, http: HttpClient, repo_id: str) -> None:
        self._http = http
        self._repo_id = repo_id

    async def exec(
        self,
        command: str,
        session_id: Optional[str] = None,
        ref: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
    ) -> ShellExecResult:
        body: dict[str, Any] = {"command": command}
        if session_id is not None:
            body["sessionId"] = session_id
        if ref is not None:
            body["ref"] = ref
        if env is not None:
            body["env"] = env
        data = await self._http.post(
            f"/repos/{self._repo_id}/shell", body
        )
        return _from_dict(ShellExecResult, data)


class ShellResource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def exec_multi(
        self,
        command: str,
        session_id: Optional[str] = None,
        mounts: Optional[list[dict[str, Any]]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> ShellMultiExecResult:
        body: dict[str, Any] = {"command": command}
        if session_id is not None:
            body["sessionId"] = session_id
        if mounts is not None:
            body["mounts"] = mounts
        if env is not None:
            body["env"] = env
        data = await self._http.post("/shell", body)
        raw_mounts = data.get("mounts", [])
        parsed_mounts = [_from_dict(ShellMount, m) for m in raw_mounts]
        return ShellMultiExecResult(
            session_id=data["sessionId"],
            stdout=data["stdout"],
            stderr=data["stderr"],
            exit_code=data["exitCode"],
            mounts=parsed_mounts,
        )

    async def destroy(self, session_id: str) -> ShellDestroyResult:
        data = await self._http.delete(f"/shell/{session_id}")
        return _from_dict(ShellDestroyResult, data)
