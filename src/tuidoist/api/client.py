"""Todoist API client wrapper."""

from __future__ import annotations

from todoist_api_python.api import TodoistAPI


class AuthError(Exception):
    """Raised when the API token is invalid or unauthorized."""


class NetworkError(Exception):
    """Raised when the API is unreachable."""


def _wrap(e: Exception) -> Exception:
    """Translate a raw API exception into AuthError or NetworkError."""
    err = str(e).lower()
    if "401" in err or "403" in err or "unauthorized" in err or "forbidden" in err:
        return AuthError("Invalid API token.")
    return NetworkError(f"Could not reach Todoist API: {e}")


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
        raise _wrap(e) from e


def get_today_tasks(token: str) -> list[dict]:
    """Fetch tasks due today.

    Returns a list of dicts with keys: id, content, priority, project_id, project_name.

    Raises:
        AuthError: If the token is invalid.
        NetworkError: If the API is unreachable.
    """
    try:
        api = TodoistAPI(token)
        tasks = [t for batch in api.filter_tasks(query="today") for t in batch]
        projects = [p for batch in api.get_projects() for p in batch]
    except Exception as e:
        raise _wrap(e) from e

    project_map = {p.id: p.name for p in projects}

    return [
        {
            "id": t.id,
            "content": t.content,
            "priority": t.priority,
            "project_id": t.project_id,
            "project_name": project_map.get(t.project_id, "Unknown"),
        }
        for t in tasks
    ]


def complete_task(token: str, task_id: str) -> None:
    """Mark a task as complete.

    Raises:
        AuthError: If the token is invalid.
        NetworkError: If the API is unreachable.
    """
    try:
        TodoistAPI(token).complete_task(task_id)
    except Exception as e:
        raise _wrap(e) from e


def add_task_today(token: str, content: str, project_id: str) -> dict:
    """Create a new task in the given project, due today.

    Returns the created task as a dict in the same shape as `get_today_tasks`
    entries (without project_name — caller should supply it).

    Raises:
        AuthError: If the token is invalid.
        NetworkError: If the API is unreachable.
    """
    try:
        task = TodoistAPI(token).add_task(
            content=content, project_id=project_id, due_string="today"
        )
    except Exception as e:
        raise _wrap(e) from e

    return {
        "id": task.id,
        "content": task.content,
        "priority": task.priority,
        "project_id": task.project_id,
    }
