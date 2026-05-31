"""TUI Today view — displays tasks due today with vim-style navigation."""

from __future__ import annotations

import pytermgui as ptg

from tuidoist.api.client import AuthError, NetworkError, get_today_tasks
from tuidoist.ui import keybindings as kb

# Todoist priority is inverted: 4 = highest (p1), 1 = lowest (p4)
PRIORITY_DISPLAY = {
    4: "[bold 210]p1[/]",
    3: "[bold 215]p2[/]",
    2: "[bold 114]p3[/]",
    1: "[243]p4[/]",
}


class TaskList:
    """Manages a selectable list of tasks with vim navigation."""

    def __init__(self, tasks: list[dict], window: ptg.Window) -> None:
        self.tasks = tasks
        self.window = window
        self.cursor = 0
        self.task_labels: list[ptg.Label] = []

    def render_tasks(self) -> list[ptg.Widget]:
        """Build label widgets for all tasks."""
        self.task_labels = []

        if not self.tasks:
            label = ptg.Label("[243]No tasks for today. Nice![/]")
            return [label]

        for i, task in enumerate(self.tasks):
            label = self._make_label(task, selected=(i == self.cursor))
            self.task_labels.append(label)

        return list(self.task_labels)

    def move(self, direction: int) -> None:
        """Move cursor up (-1) or down (+1)."""
        if not self.tasks:
            return

        old = self.cursor
        self.cursor = max(0, min(len(self.tasks) - 1, self.cursor + direction))

        if old != self.cursor:
            self.task_labels[old].value = self._format_task(
                self.tasks[old], selected=False
            )
            self.task_labels[self.cursor].value = self._format_task(
                self.tasks[self.cursor], selected=True
            )

    def _make_label(self, task: dict, selected: bool) -> ptg.Label:
        return ptg.Label(self._format_task(task, selected))

    @staticmethod
    def _format_task(task: dict, selected: bool) -> str:
        priority = PRIORITY_DISPLAY.get(task["priority"], "")
        project = f"[243]{task['project_name']}[/]"
        content = task["content"]
        indicator = "[bold 183]▸[/] " if selected else "  "
        return f"{indicator}{priority} {content}  {project}"


def show_today(manager: ptg.WindowManager, token: str) -> None:
    """Display the Today task view."""

    try:
        tasks = get_today_tasks(token)
    except AuthError:
        from tuidoist.config.config import Config, save
        from tuidoist.ui.views.onboarding import show_onboarding

        # Token is stale/revoked — clear config and restart onboarding
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
        ptg.Label("[bold 183]Today[/]"),
        "",
        box_type=ptg.boxes.DOUBLE,
        overflow=ptg.Overflow.SCROLL,
    )

    task_list = TaskList(tasks, window)
    for widget in task_list.render_tasks():
        window += widget

    window += ""
    window += ptg.Label("[243]j/k navigate  q quit[/]")

    manager.bind(kb.UP, lambda *_: task_list.move(-1))
    manager.bind(kb.DOWN, lambda *_: task_list.move(1))
    manager.bind(kb.QUIT, lambda *_: manager.stop())

    manager.add(window, assign="main")
