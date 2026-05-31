"""TUI onboarding view — guides user through API token setup."""

from __future__ import annotations

import pytermgui as ptg

from tuidoist.api.client import AuthError, NetworkError, validate_token
from tuidoist.config.config import Config, save
from tuidoist.ui import keybindings as kb


def show_onboarding(manager: ptg.WindowManager) -> None:
    """Display the onboarding window for API token entry."""

    token_field = ptg.InputField(prompt="API Token: ")
    status_label = ptg.Label("")

    def on_submit(*_args: object) -> None:
        token = token_field.value.strip()
        if not token:
            status_label.value = "[bold 210]Please enter your API token.[/]"
            return

        status_label.value = "[bold 243]Validating token...[/]"

        try:
            validate_token(token)
        except AuthError:
            status_label.value = "[bold 210]Invalid token. Please try again.[/]"
            return
        except NetworkError as e:
            status_label.value = f"[bold 210]{e}[/]"
            return

        config = Config(api_token=token)
        save(config)

        from tuidoist.ui.views.today import show_today

        # Clear onboarding-scoped manager bindings before transitioning so
        # leftover handlers don't fire against a removed window.
        manager.bind(kb.SELECT, lambda *_: None)

        # Show the next view BEFORE removing onboarding, and disable autostop
        # on the removal. pytermgui's animated remove runs on the compositor
        # thread and calls manager.stop() the moment _windows hits length 0.
        # If show_today blocks on a network call, the animation can complete
        # first, stopping the manager and silently exiting the app.
        show_today(manager, token)
        manager.remove(window, autostop=False)

    window = ptg.Window(
        "",
        ptg.Label("[bold 183]Welcome to Tuidoist[/]"),
        "",
        ptg.Label("Enter your Todoist API token to get started."),
        ptg.Label("[243]Find it at: Settings → Integrations → Developer[/]"),
        "",
        token_field,
        "",
        ptg.Button("Connect", onclick=on_submit),
        "",
        status_label,
        "",
        ptg.Label("[243]q to quit[/]"),
        box_type=ptg.boxes.DOUBLE,
        is_modal=True,
        overflow=ptg.Overflow.SCROLL,
    )
    window.relative_width = 0.5
    window.center()
    manager.bind(kb.QUIT, lambda *_: manager.stop())
    manager.bind(kb.SELECT, lambda *_: on_submit())
    manager.add(window)
