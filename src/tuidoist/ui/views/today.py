"""TUI Today view — project-grouped tasks with completion and inline quick-add."""

from __future__ import annotations

import pytermgui as ptg

from tuidoist.api.client import (
    AuthError,
    NetworkError,
    add_task_today,
    complete_task,
    get_today_tasks,
)
from tuidoist.ui import keybindings as kb

# Todoist priority is inverted: 4 = highest (p1), 1 = lowest (p4)
PRIORITY_DISPLAY = {
    4: "[bold 210]p1[/]",
    3: "[bold 215]p2[/]",
    2: "[bold 114]p3[/]",
    1: "[243]p4[/]",
}

HELP_TEXT = "[243]j/k navigate  enter complete  n new task  q quit[/]"
INPUT_HELP_TEXT = "[243]enter save  esc cancel[/]"
RIGHT = ptg.HorizontalAlignment.RIGHT


def _group_tasks(tasks: list[dict]) -> dict[str, list[dict]]:
    """Group tasks by project_name, preserving insertion order."""
    groups: dict[str, list[dict]] = {}
    for task in tasks:
        groups.setdefault(task["project_name"], []).append(task)
    return groups


def _format_task(task: dict, selected: bool) -> str:
    priority = PRIORITY_DISPLAY.get(task["priority"], "")
    content = task["content"]
    indicator = "[bold 183]▸[/] " if selected else "  "
    return f"{indicator}{priority} {content}"


def _format_header(project_name: str) -> str:
    return f"[bold 183]{project_name}[/]"


class TodayView:
    """Renders and manages the grouped Today view."""

    def __init__(
        self,
        manager: ptg.WindowManager,
        window: ptg.Window,
        token: str,
        tasks: list[dict],
    ) -> None:
        self.manager = manager
        self.window = window
        self.token = token
        self.groups = _group_tasks(tasks)
        self.cursor_task_id: str | None = self._first_task_id()
        self.input_mode = False
        self.input_field: ptg.InputField | None = None
        self.input_after_task_id: str | None = None
        self.input_project_name: str | None = None
        self.rebuild()

    # --- helpers ---

    def _ordered_task_ids(self) -> list[str]:
        return [t["id"] for tasks in self.groups.values() for t in tasks]

    def _first_task_id(self) -> str | None:
        ids = self._ordered_task_ids()
        return ids[0] if ids else None

    def _find_task(self, task_id: str) -> tuple[str, dict] | None:
        for project_name, tasks in self.groups.items():
            for task in tasks:
                if task["id"] == task_id:
                    return project_name, task
        return None

    # --- rendering ---

    def rebuild(self) -> None:
        """Rebuild the entire window widget list from current state."""
        widgets: list[ptg.Widget] = [
            ptg.Label("[bold 183]Today[/]", parent_align=ptg.HorizontalAlignment.LEFT),
            ptg.Label(""),
        ]

        if not self.groups and not self.input_mode:
            widgets.append(ptg.Label("[243]No tasks for today. Nice![/]"))
        else:
            for project_name, tasks in self.groups.items():
                widgets.append(
                    ptg.Label(_format_header(project_name))
                )
                for task in tasks:
                    selected = task["id"] == self.cursor_task_id and not self.input_mode
                    widgets.append(
                        ptg.Label(_format_task(task, selected), parent_align=RIGHT)
                    )
                    if (
                        self.input_mode
                        and self.input_after_task_id == task["id"]
                        and self.input_field is not None
                    ):
                        widgets.append(self.input_field)
                widgets.append(ptg.Label(""))

            # Handle "new task in empty project" (no tasks left, but input still active)
            if (
                self.input_mode
                and self.input_after_task_id is None
                and self.input_field is not None
                and self.input_project_name is not None
            ):
                widgets.append(ptg.Label(_format_header(self.input_project_name)))
                widgets.append(self.input_field)
                widgets.append(ptg.Label(""))

        widgets.append(
            ptg.Label(INPUT_HELP_TEXT if self.input_mode else HELP_TEXT)
        )
        self.window.set_widgets(widgets)

        # Focus the input field so it receives character keystrokes.
        if self.input_mode and self.input_field is not None:
            try:
                self.window.select(0)
            except (IndexError, TypeError):
                pass

    # --- navigation ---

    def move(self, direction: int) -> None:
        if self.input_mode:
            return
        ids = self._ordered_task_ids()
        if not ids:
            return
        try:
            idx = ids.index(self.cursor_task_id) if self.cursor_task_id else 0
        except ValueError:
            idx = 0
        new_idx = max(0, min(len(ids) - 1, idx + direction))
        if new_idx == idx:
            return
        self.cursor_task_id = ids[new_idx]
        self.rebuild()

    # --- actions ---

    def complete_current(self) -> None:
        if self.input_mode or self.cursor_task_id is None:
            return
        found = self._find_task(self.cursor_task_id)
        if found is None:
            return
        project_name, task = found

        try:
            complete_task(self.token, task["id"])
        except (AuthError, NetworkError):
            # Swallow for now; a status line is out of scope for this slice.
            return

        # Determine next cursor before mutating.
        ids = self._ordered_task_ids()
        idx = ids.index(task["id"])
        next_ids = [tid for tid in ids if tid != task["id"]]
        if next_ids:
            self.cursor_task_id = next_ids[min(idx, len(next_ids) - 1)]
        else:
            self.cursor_task_id = None

        self.groups[project_name].remove(task)
        if not self.groups[project_name]:
            del self.groups[project_name]

        self.rebuild()

    def begin_new_task(self) -> None:
        if self.input_mode or self.cursor_task_id is None:
            return
        found = self._find_task(self.cursor_task_id)
        if found is None:
            return
        project_name, task = found

        self.input_mode = True
        self.input_after_task_id = task["id"]
        self.input_project_name = project_name
        self.input_field = ptg.InputField(prompt="  + ")

        # Unbind nav keys so the field can capture characters like 'j', 'k', 'n', 'q'.
        for key in (kb.UP, kb.DOWN, "n", kb.QUIT):
            try:
                self.manager.unbind(key)
            except KeyError:
                pass

        self.rebuild()

    def submit_new_task(self) -> None:
        if not self.input_mode or self.input_field is None:
            return
        content = self.input_field.value.strip()
        project_name = self.input_project_name
        if not content or project_name is None:
            self.cancel_new_task()
            return

        # Need a project_id to send to the API. Look it up from any existing
        # task in that project, or from the task we anchored on.
        project_id: str | None = None
        if self.input_after_task_id is not None:
            found = self._find_task(self.input_after_task_id)
            if found is not None:
                project_id = found[1]["project_id"]
        if project_id is None and self.groups.get(project_name):
            project_id = self.groups[project_name][0]["project_id"]

        if project_id is None:
            self.cancel_new_task()
            return

        try:
            new_task = add_task_today(self.token, content, project_id)
        except (AuthError, NetworkError):
            self.cancel_new_task()
            return

        new_task["project_name"] = project_name
        self.groups.setdefault(project_name, []).append(new_task)
        self.cursor_task_id = new_task["id"]
        self._exit_input_mode()
        self.rebuild()

    def cancel_new_task(self) -> None:
        if not self.input_mode:
            return
        self._exit_input_mode()
        self.rebuild()

    def _exit_input_mode(self) -> None:
        self.input_mode = False
        self.input_field = None
        self.input_after_task_id = None
        self.input_project_name = None
        # Restore nav keys.
        _bind_nav_keys(self.manager, self)


def _bind_nav_keys(manager: ptg.WindowManager, view: TodayView) -> None:
    manager.bind(kb.UP, lambda *_: view.move(-1))
    manager.bind(kb.DOWN, lambda *_: view.move(1))
    manager.bind("n", lambda *_: view.begin_new_task())
    manager.bind(kb.QUIT, lambda *_: manager.stop())


def show_today(manager: ptg.WindowManager, token: str) -> None:
    """Display the project-grouped Today task view."""

    try:
        tasks = get_today_tasks(token)
    except AuthError:
        from tuidoist.config.config import Config, save
        from tuidoist.ui.views.onboarding import show_onboarding

        save(Config())
        error_window = ptg.Window(
            ptg.Label(
                "[bold 210]Token expired or revoked. Please re-authenticate.[/]"
            ),
            "",
            ptg.Button(
                "OK",
                onclick=lambda *_: (
                    show_onboarding(manager),
                    manager.remove(error_window, autostop=False),
                ),
            ),
            "",
            ptg.Label("[243]q to quit[/]"),
            box_type=ptg.boxes.DOUBLE,
            is_modal=True,
        )
        manager.bind(kb.QUIT, lambda *_: manager.stop())
        manager.add(error_window)
        return
    except NetworkError as e:
        window = ptg.Window(
            ptg.Label(f"[bold 210]{e}[/]"),
            "",
            ptg.Button("Quit", onclick=lambda *_: manager.stop()),
            "",
            ptg.Label("[243]q to quit[/]"),
            box_type=ptg.boxes.DOUBLE,
            is_modal=True,
        )
        manager.bind(kb.QUIT, lambda *_: manager.stop())
        manager.add(window)
        return

    window = ptg.Window(
        box_type=ptg.boxes.DOUBLE,
        overflow=ptg.Overflow.SCROLL,
    )

    view = TodayView(manager, window, token, tasks)

    _bind_nav_keys(manager, view)

    # Enter is context-sensitive: complete task, or submit new task input.
    def on_select(*_args: object) -> None:
        if view.input_mode:
            view.submit_new_task()
        else:
            view.complete_current()

    def on_back(*_args: object) -> None:
        if view.input_mode:
            view.cancel_new_task()

    manager.bind(kb.SELECT, on_select)
    manager.bind(kb.BACK, on_back)

    manager.add(window, assign="main")
