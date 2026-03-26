from __future__ import annotations


class GitForgeError(Exception):
    """Base error for all GitForge API errors."""

    def __init__(self, status: int, code: str, message: str) -> None:
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class RefUpdateError(GitForgeError):
    """Thrown when a ref update fails due to CAS conflict (branch moved)."""

    def __init__(self, message: str, current_sha: str) -> None:
        self.current_sha = current_sha
        super().__init__(409, "branch_moved", message)
