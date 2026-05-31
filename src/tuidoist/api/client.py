"""Todoist API client wrapper."""

from __future__ import annotations

from todoist_api_python.api import TodoistAPI


class AuthError(Exception):
    """Raised when the API token is invalid or unauthorized."""


class NetworkError(Exception):
    """Raised when the API is unreachable."""


def validate_token(token: str) -> None:
    """Validate a Todoist API token by attempting to fetch projects.

    Raises:
        AuthError: If the token is invalid.
        NetworkError: If the API is unreachable.
    """
    try:
        api = TodoistAPI(token)
        list(api.get_projects())
    except Exception as e:
        err = str(e).lower()
        if "401" in err or "403" in err or "unauthorized" in err or "forbidden" in err:
            raise AuthError("Invalid API token.") from e
        raise NetworkError(f"Could not reach Todoist API: {e}") from e


def get_today_tasks(token: str) -> list[dict]:
    """Fetch tasks due today.

    Returns a list of dicts with keys: id, content, priority, project_name.

    Raises:
        AuthError: If the token is invalid.
        NetworkError: If the API is unreachable.
    """
    try:
        api = TodoistAPI(token)
        tasks = [t for batch in api.filter_tasks(query="today") for t in batch]
        projects = [p for batch in api.get_projects() for p in batch]
    except Exception as e:
        err = str(e).lower()
        if "401" in err or "403" in err or "unauthorized" in err or "forbidden" in err:
            raise AuthError("Invalid API token.") from e
        raise NetworkError(f"Could not reach Todoist API: {e}") from e

    project_map = {p.id: p.name for p in projects}

    return [
        {
            "id": t.id,
            "content": t.content,
            "priority": t.priority,
            "project_name": project_map.get(t.project_id, "Unknown"),
        }
        for t in tasks
    ]
